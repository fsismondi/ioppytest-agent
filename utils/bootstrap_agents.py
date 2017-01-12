import logging
import os
import json
import pika

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
queue_name = 'unittest_packet_router'

# rewrite default values with ENV variables
AMQP_SERVER = str(os.environ['AMQP_SERVER'])
AMQP_USER = str(os.environ['AMQP_USER'])
AMQP_PASS = str(os.environ['AMQP_PASS'])
AMQP_VHOST = str(os.environ['AMQP_VHOST'])
AMQP_EXCHANGE = str(os.environ['AMQP_EXCHANGE'])

print('Env vars for AMQP connection succesfully imported')

print(json.dumps(
        {
            'server': AMQP_SERVER,
            'session': AMQP_VHOST,
            'user': AMQP_USER,
            'pass': '#' * len(AMQP_PASS),
            'exchange': AMQP_EXCHANGE
        }
))

connection = pika.BlockingConnection(
        pika.connection.URLParameters(
                'amqp://%s:%s@%s/%s'
                %(AMQP_USER,
                  AMQP_PASS,
                  AMQP_SERVER,
                  AMQP_VHOST)
        )
)

channel = connection.channel()
channel.confirm_delivery()

d = {
    "_type": "tun.start",
    "ipv6_host": ":1",
    "ipv6_prefix": "bbbb"
}

logging.debug("Let's start the bootstrap the agents")

channel.basic_publish(exchange='default',
                       routing_key='control.tun.toAgent.agent1',
                       mandatory=True,
                       body=json.dumps(d))

d["ipv6_host"] = ":2"
channel.basic_publish(exchange='default',
                       routing_key='control.tun.toAgent.agent2',
                       mandatory=True,
                       body=json.dumps(d))

d["ipv6_host"] = ":3"
channel.basic_publish(exchange='default',
                       routing_key='control.tun.toAgent.agent_TT',
                       mandatory=True,
                       body=json.dumps(d))