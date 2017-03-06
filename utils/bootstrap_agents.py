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

# TODO wait for session bootsrap message and get agents names from there?
AGENT_1_ID = 'coap_client_agent'
AGENT_2_ID = 'coap_server_agent'
AGENT_TT_ID = 'agent_TT'

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

channel.basic_publish(
        exchange=AMQP_EXCHANGE,
        routing_key='control.tun.toAgent.%s'%AGENT_1_ID,
        mandatory=True,
        properties=pika.BasicProperties(
            content_type='application/json',
        ),
        body=json.dumps(d)
)

d["ipv6_host"] = ":2"
channel.basic_publish(
        exchange=AMQP_EXCHANGE,
        routing_key='control.tun.toAgent.%s'%AGENT_1_ID,
        mandatory=True,
        properties=pika.BasicProperties(
                content_type='application/json',
        ),
        body=json.dumps(d)
)

d["ipv6_host"] = ":3"
channel.basic_publish(
        exchange=AMQP_EXCHANGE,
        routing_key='control.tun.toAgent.%s'%AGENT_TT_ID,
        mandatory=True,
        properties=pika.BasicProperties(
            content_type='application/json',
        ),
        body=json.dumps(d)
)

