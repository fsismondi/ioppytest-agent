import logging
import sys
import os
import json
import pika
import time

logging.getLogger('pika').setLevel(logging.INFO)
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
queue_name = 'unittest_packet_router'

# rewrite default values with ENV variables
AMQP_URL = str(os.environ['AMQP_URL'])
AMQP_EXCHANGE = str(os.environ['AMQP_EXCHANGE'])

def publish_tun_start(channel, agent_id, ipv6_host, ipv6_prefix):
    d = {
        "_type": "tun.start",
        "name": agent_id,
        "ipv6_host": ipv6_host,
        "ipv6_prefix": ipv6_prefix,
    }

    channel.basic_publish(
            exchange=AMQP_EXCHANGE,
            routing_key='control.tun.toAgent.%s' % agent_id,
            mandatory=True,
            properties=pika.BasicProperties(
                    content_type='application/json',
            ),
            body=json.dumps(d)
    )

def check_response(channel,queue_name, agent_id):
    method, header, body = channel.basic_get(queue=queue_name)
    if body is not None:
        try:
            body_dict = json.loads(body.decode('utf-8'))
            if body_dict['_type'] == "tun.started" and body_dict['name']==agent_id:
                return True
        except Exception as e:
            logging.error(str(e))
            pass

    return False


if __name__ == "__main__":

    try:
        agent_id = sys.argv[1]
        ipv6_prefix = sys.argv[2]
        ipv6_host = sys.argv[3]

    except:
        print("Error, please execute as: python3 ...bootstrap_agent.py <agent_name>  <ipv6_prefix>  <ipv6_host>")
        print("Example python3 ...bootstrap_agent.py coap_client_agent  bbbb  :1 ")
        sys.exit(1)


    connection = pika.BlockingConnection(pika.connection.URLParameters(AMQP_URL))

    channel = connection.channel()



    agent_event_q = 'agent_bootstrap'
    result = channel.queue_declare(queue=agent_event_q)
    callback_queue = result.method.queue

    # lets purge in case there are old messages
    channel.queue_purge(agent_event_q)

    channel.queue_bind(exchange=AMQP_EXCHANGE,
                       queue=callback_queue,
                       routing_key='control.tun.fromAgent.%s'%agent_id)

    for i in range (1,4):
        logging.debug("Let's start the bootstrap the agent %s try number %d" %(agent_id,i))
        publish_tun_start(channel, agent_id, ipv6_host, ipv6_prefix)
        time.sleep(4)
        if check_response(channel,agent_event_q, agent_id):
            logging.debug("Agent tun bootstrapped")
            sys.exit(0)
        elif i < 3:
            pass
        else:
            logging.error("Agent tun bootstrapping mechanism not working, check that the agent was launched correctly")
            sys.exit(1)

