import json
import logging
import os
import pika
import pytest

log = logging.getLogger(__name__)

try:
    AMQP_URL = str(os.environ['AMQP_URL'])
    AMQP_EXCHANGE = str(os.environ['AMQP_EXCHANGE'])
except:
    AMQP_URL = 'amqp://guest:guest@localhost/'
    AMQP_EXCHANGE = 'amq.topic'

@pytest.fixture
def producer():
    connection = pika.BlockingConnection(
        pika.connection.URLParameters(AMQP_URL))
    channel = connection.channel()
    channel.confirm_delivery()
    return channel


def test_ping(producer):
    """
    Launch a ping towards localhost through the agent

    Returns:

    """
    d = {"version": "IPv6",
         "count": 1,
         "host": "localhost",
         "payload": "cafe",
         "interface": "tun0"}
    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.ping.coucou.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_http(producer):
    """

    Returns:

    """
    d = {"verb": "GET",
         "url": "http://f-interop.paris.inria.fr",
         "data": {}
         }
    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.http.coucou.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_zmq(producer):
    """

    Returns:

    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "sender": "f-interop agent",
                     "data": {
                         "action": ["imageCommand", "6pAdd", "[6,7]"],
                         "serialPort": "/dev/ttyUSB0"}}}
    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_control_tun_start(producer):
    """
    Starts tun interface in agent 1 and agent 2
    TODO: check which queues exist in RMQ and get that way the quantity of agents on the bus?
    Returns:

    """
    d={
        "_type": "tun.start",
        "ipv6_host": ":1",
        "ipv6_prefix": "bbbb"
    }

    log.debug("Let's start the bootstrap the agents")
    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.tun.toAgent.agent1',
                           mandatory=True,
                           body=json.dumps(d))

    d["ipv6_host"] = ":2"
    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.tun.toAgent.agent2',
                           mandatory=True,
                           body=json.dumps(d))

