import logging
import sys
import os
import json
import pika
import argparse
import time

logging.getLogger('pika').setLevel(logging.INFO)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
queue_name = 'unittest_packet_router'


def publish_tun_start(channel, agent_id, ipv6_host, ipv6_prefix, ipv6_no_forwarding=False):
    d = {
        "_type": "tun.start",
        "name": agent_id,
        "ipv6_host": ipv6_host,
        "ipv6_prefix": ipv6_prefix,
        "ipv6_no_forwarding": ipv6_no_forwarding
    }

    channel.basic_publish(
        exchange='default',
        routing_key='control.tun.toAgent.%s' % agent_id,
        mandatory=True,
        properties=pika.BasicProperties(
            content_type='application/json',
        ),
        body=json.dumps(d)
    )


def publish_tun_bootrap_success(channel, agent_id):
    d = {
        "_type": "agent.configured",
        "description": "Event agent successfully CONFIGURED",
        "name": agent_id,
    }

    channel.basic_publish(
        exchange='default',
        routing_key='control.session',
        mandatory=True,
        properties=pika.BasicProperties(
            content_type='application/json',
        ),
        body=json.dumps(d)
    )


def check_response(channel, queue_name, agent_id):
    method, header, body = channel.basic_get(queue=queue_name)
    if body is not None:
        try:
            body_dict = json.loads(body.decode('utf-8'))
            if body_dict['_type'] == "tun.started" and body_dict['name'] == agent_id:
                return True
        except Exception as e:
            logging.error(str(e))
            pass

    return False


def bootstrap(amqp_url, amqp_exchange, agent_id, ipv6_host, ipv6_prefix, ipv6_no_forwarding):
    connection = pika.BlockingConnection(pika.connection.URLParameters(AMQP_URL))
    channel = connection.channel()
    agent_event_q = 'agent_bootstrap'
    result = channel.queue_declare(queue=agent_event_q)
    callback_queue = result.method.queue

    # lets purge in case there are old messages
    channel.queue_purge(agent_event_q)

    channel.queue_bind(exchange=AMQP_EXCHANGE,
                       queue=callback_queue,
                       routing_key='control.tun.fromAgent.%s' % agent_id)

    for i in range(1, 4):
        logging.debug("Let's start the bootstrap the agent %s try number %d" % (agent_id, i))
        publish_tun_start(channel, agent_id, ipv6_host, ipv6_prefix, ipv6_no_forwarding)
        time.sleep(4)
        if check_response(channel, agent_event_q, agent_id):
            logging.debug("Agent tun bootstrapped")
            publish_tun_bootrap_success(channel, agent_id)
        elif i < 3:
            pass
        else:
            logging.error("Agent tun bootstrapping mechanism not working, check that the agent was launched correctly")


if __name__ == "__main__":

    # rewrite default values with ENV variables
    AMQP_URL = str(os.environ['AMQP_URL'])
    AMQP_EXCHANGE = str(os.environ['AMQP_EXCHANGE'])

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("agent_name", help="Name of the agent")
        parser.add_argument("ipv6_prefix", help="ipv6 prefix")
        parser.add_argument("ipv6_host", help="ipv6 host network")
        parser.add_argument("-nf", "--no_forwarding", help="activate or not IPv6 forwarding", action="store_true")
        args = parser.parse_args()

        agent_id = args.agent_name
        ipv6_prefix = args.ipv6_prefix
        ipv6_host = args.ipv6_host
        ipv6_no_forwarding = args.no_forwarding

    except:
        print("Error, please see help (-h)")
        sys.exit(1)

    bootstrap(AMQP_URL, AMQP_EXCHANGE, agent_id, ipv6_host, ipv6_prefix, ipv6_no_forwarding)
