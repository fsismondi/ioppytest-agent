import logging
import sys
import os
import json
import pika
import argparse
import time

# for using it as library and as a __main__
try:
    from messages import MsgAgentTunStarted, MsgAgentTunStart, Message
except:
    from .messages import MsgAgentTunStarted, MsgAgentTunStart, Message

logging.getLogger('pika').setLevel(logging.INFO)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
RETRY_PERIOD = 1


def publish_tun_start(exchange, channel, agent_id, ipv6_host, ipv6_prefix, ipv6_no_forwarding=False):
    msg = MsgAgentTunStart(
        name=agent_id,
        ipv6_host=ipv6_host,
        ipv6_prefix=ipv6_prefix,
        ipv6_no_forwarding=ipv6_no_forwarding
    )

    channel.basic_publish(
        exchange=exchange,
        routing_key=msg.routing_key.replace('*', agent_id),
        mandatory=True,
        properties=pika.BasicProperties(
            content_type='application/json',
        ),
        body=msg.to_json()
    )


def check_response(channel, queue_name, agent_id):
    method, header, body = channel.basic_get(queue=queue_name)
    if body is not None:

        try:
            msg = Message.load_from_pika(method, header, body)
            print('got message: %s' % repr(msg))
            if isinstance(msg, MsgAgentTunStarted) and msg.name == agent_id:
                return True
        except Exception as e:
            logging.error(str(e))
            pass

    return False


def bootstrap(amqp_url, amqp_exchange, agent_id, ipv6_host, ipv6_prefix, ipv6_no_forwarding):
    connection = pika.BlockingConnection(pika.connection.URLParameters(amqp_url))
    channel = connection.channel()
    agent_event_q = 'agent_bootstrap|%s' % agent_id
    result = channel.queue_declare(queue=agent_event_q, auto_delete=True)
    callback_queue = result.method.queue

    # lets purge in case there are old messages
    channel.queue_purge(agent_event_q)

    channel.queue_bind(exchange=amqp_exchange,
                       queue=callback_queue,
                       routing_key=MsgAgentTunStarted.routing_key.replace('*', agent_id)
                       )

    try:
        for i in range(1, 4):
            logging.debug("Let's start the bootstrap the agent %s try number %d" % (agent_id, i))
            publish_tun_start(amqp_exchange, channel, agent_id, ipv6_host, ipv6_prefix, ipv6_no_forwarding)
            time.sleep(RETRY_PERIOD)
            if check_response(channel, agent_event_q, agent_id):
                logging.debug("Agent tun bootstrapped")
                break
            elif i < 3:
                pass
            else:
                logging.warning(
                    "Agent didnt answer to bootstrap command, is agent up? it is already bootstrapped?")

    except Exception as e:
        logging.error("Agent tun bootstrapping mechanism not working, exception %s" % e)

    finally:
        channel.queue_delete(agent_event_q)


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
