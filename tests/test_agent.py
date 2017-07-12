import json
import logging
import os
import pika
import pytest

log = logging.getLogger(__name__)


"""
primer from 6p openwsn-fw/build/OpenMote-CC2538_armgcc/openstack/02b-MAChigh/sixtop.h

//=========================== define ==========================================
// 6P version
#define IANA_6TOP_6P_VERSION   0x01
// 6P command Id
#define IANA_6TOP_CMD_NONE     0x00
#define IANA_6TOP_CMD_ADD      0x01 // CMD_ADD      | add one or more cells
#define IANA_6TOP_CMD_DELETE   0x02 // CMD_DELETE   | delete one or more cells
#define IANA_6TOP_CMD_COUNT    0x03 // CMD_COUNT    | count scheduled cells
#define IANA_6TOP_CMD_LIST     0x04 // CMD_LIST     | list the scheduled cells
#define IANA_6TOP_CMD_CLEAR    0x05 // CMD_CLEAR    | clear all cells
// 6P return code
#define IANA_6TOP_RC_SUCCESS   0x06 // RC_SUCCESS  | operation succeeded
#define IANA_6TOP_RC_VER_ERR   0x07 // RC_VER_ERR  | unsupported 6P version
#define IANA_6TOP_RC_SFID_ERR  0x08 // RC_SFID_ERR | unsupported SFID
#define IANA_6TOP_RC_BUSY      0x09 // RC_BUSY     | handling previous request
#define IANA_6TOP_RC_RESET     0x0a // RC_RESET    | abort 6P transaction
#define IANA_6TOP_RC_ERR       0x0b // RC_ERR      | operation failed

// states of the sixtop-to-sixtop state machine
typedef enum {
    // ready for next event
    SIX_IDLE                            = 0x00,
    // sending
    SIX_SENDING_REQUEST                 = 0x01,
    // waiting for SendDone confirmation
    SIX_WAIT_ADDREQUEST_SENDDONE        = 0x02,
    SIX_WAIT_DELETEREQUEST_SENDDONE     = 0x03,
    SIX_WAIT_COUNTREQUEST_SENDDONE      = 0x04,
    SIX_WAIT_LISTREQUEST_SENDDONE       = 0x05,
    SIX_WAIT_CLEARREQUEST_SENDDONE      = 0x06,
    // waiting for response from the neighbor
    SIX_WAIT_ADDRESPONSE                = 0x07,
    SIX_WAIT_DELETERESPONSE             = 0x08,
    SIX_WAIT_COUNTRESPONSE              = 0x09,
    SIX_WAIT_LISTRESPONSE               = 0x0a,
    SIX_WAIT_CLEARRESPONSE              = 0x0b,

    // response senddone
    SIX_REQUEST_RECEIVED                = 0x0c,
    SIX_WAIT_RESPONSE_SENDDONE          = 0x0d
} six2six_state_t;

"""
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


def test_6p_add(producer):
    """

    Used in 6TiSCH testing.
    TODO: Implemented by which nodes? DAG ? 6N ?

    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "6pAdd", "[6,7]"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_6p_count(producer):
    """

    TODO: Write docs
    Used in 6TiSCH testing.
    TODO: Implemented by which nodes? DAG ? 6N ?

    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "6pCount", "0"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_6p_list(producer):
    """
    TODO: Write docs
    Used in 6TiSCH testing.

    TODO: Implemented by which nodes? DAG ? 6N ?

    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "6pList", "0"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_6p_clear(producer):
    """
    TODO: Write docs
    Used in 6TiSCH testing.
    TODO: Implemented by which nodes? DAG ? 6N ?

    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "6pClear", "0"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_6p_delete(producer):
    """

    TODO: Write docs
    Use 3 arguments
    Used in 6TiSCH testing.
    TODO: Implemented by which nodes? DAG ? 6N ?

    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "6pDelete", "[6,7]"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_6p_answers(producer):
    """
    enable/disable 6P response (set value to 1 to enable, 0 to disable)
    Test if 6P answers can be enable/disabled to create timeouts.
    Used in 6TiSCH testing.
    TODO: Implemented by which nodes? DAG ? 6N ?
    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "6pResponse", "1"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_send_dio(producer):
    """

    Used in 6TiSCH testing.
    set the period at the which the device sends DIOs (value in milli-seconds)
    TODO: Implemented by which nodes? DAG ? 6N ?
    Returns:

    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "dioPeriod", "1000"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_send_dao(producer):
    """

    Used in 6TiSCH testing.
    TODO: Implemented by which nodes? DAG ? 6N ?
    set the period at the which the device sends DAOs (value in milli-seconds)
    Returns:

    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "daoPeriod", "1000"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           body=json.dumps(d))


def test_send_keep_alive(producer):
    """
    TODO: Implemented by which nodes? DAG ? 6N ?
    Used in 6TiSCH testing.
    set the timeout which the device send a keepAlive(value in slots)
    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "kaPeriod", "1000"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           body=json.dumps(d))


def test_channel(producer):
    """

    set the communication channel
    TODO: Implemented by which nodes? DAG ? 6N ?
    Used in 6TiSCH testing.
    Returns:

    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "channel", "6"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

    producer.basic_publish(exchange=AMQP_EXCHANGE,
                           routing_key='control.zeromq.req.client',
                           mandatory=True,
                           body=json.dumps(d))


def test_control_ebperiod(producer):
    """
    set the period at the which the device sends enhanced beacons (value in seconds)
    Used in 6TiSCH testing.
    TODO: Implemented by which nodes? DAG ? 6N ?
    Returns:

    """
    d = {"zmq_socket_type": "req",
         "url": "tcp://localhost:60000",
         "payload": {"signal": "cmdToMote",
                     "data": {
                         "action": ["imageCommand", "ebPeriod", "2"],
                         "serialPort": "/dev/ttyUSB0"
                     },
                     "sender": "f-interop agent"}}

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

