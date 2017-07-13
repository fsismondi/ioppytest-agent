"""
Send ZMQ messages
"""
import json
import pdb
from multiprocessing import Process

from kombu import Connection
from kombu import Producer

__version__ = (0, 0, 1)

import logging
import zmq

from .base import BaseController, BaseConsumer

log = logging.getLogger(__name__)


class ZMQConsumer(BaseConsumer):
    """
    AMQP helper
    """

    def __init__(self, user, password, session, server, exchange, name, consumer_name):
        super(ZMQConsumer, self).__init__(user,
                                          password,
                                          session,
                                          server,
                                          exchange,
                                          name,
                                          consumer_name)

        self.dispatcher = {
            "push": self.handle_push,
            "req": self.handle_req,
            "sub": self.handle_sub,
            "list": self.handle_list
        }

        self.context = zmq.Context()

    def handle_control(self, body, message):
        """

        Args:
            msg:

        Returns:

        """
        msg = None
        try:
            msg = json.loads(body)
            self.log.debug(message)
        except ValueError as e:
            message.ack()
            self.log.error(e)
            self.log.error("Incorrect message: {0}".format(body))
            return

        if "zmq_socket_type" in msg.keys():
            if msg["zmq_socket_type"] in self.dispatcher.keys():
                self.dispatcher[msg["zmq_socket_type"]](msg)
            else:
                self.log.debug("Not supported action")
        else:
            self.log.debug('No zmq_socket_type')

    def handle_push(self, msg):
        self.log.debug("LET'S PUSH EVENT TO A PUSH SOCKET")
        push_socket = self.context.socket(zmq.PUSH)

    def handle_sub(self, msg):
        self.log.debug("Let's handle sub socket")
        p = Process(target=self.do_sub, args=(msg,))
        p.start()

    def handle_req(self, msg):
        self.log.debug("Let's handle req socket")
        p = Process(target=self.do_req, args=(msg,))
        p.start()

    def handle_list(self, msg):
        self.log.debug("Let's handle a list")

    def do_req(self, msg):
        required_keys = {"url", "payload"}
        if set(msg.keys()).issuperset(required_keys):
            # Let's open a RMQ message producer
            producer = Producer(Connection(self.server_url,
                                           transport_options={'confirm_publish': True}))
            # Let's open the ZMQ socket
            req_socket = self.context.socket(zmq.REQ)
            self.log.info("Trying to connect to %s" % msg["url"])
            req_socket.connect(msg["url"])
            req_socket.send_json(msg["payload"])
            self.log.debug("Sent the JSON")
            rep = req_socket.recv_json()
            self.log.debug("Received the JSON %s" % rep)
            producer.publish(rep,
                             exchange=self.exchange,
                             routing_key="data.zeromq.rep")

        else:
            self.log.error("Incorrect keys: %s while expecting %s" % (msg.keys(), required_keys))

    def handle_data(self, body, message):
        """

        Args:
            msg:

        Returns:

        """
        self.log.debug("HANDLE DATA from zeromq")
        self.log.debug(("Payload", message.payload))
        self.log.debug(("Properties", message.properties))
        self.log.debug(("Headers", message.headers))
        self.log.debug(("body", message.body))

    def do_sub(self, msg):
        """

        Args:
            msg:

        Returns:

        """
        required_keys = {"url"}
        if set(msg.keys()).issuperset(required_keys):
            # Let's open a RMQ message producer
            producer = Producer(Connection(self.server_url,
                                           transport_options={'confirm_publish': True}))
            # Let's open the ZMQ socket
            sub_socket = self.context.socket(zmq.SUB)
            sub_socket.connect(msg["url"])
            sub_socket.setsockopt(zmq.SUBSCRIBE, "")
            while True:
                string = sub_socket.recv_json()
                self.log.debug(string)
                producer.publish(string,
                                 exchange=self.exchange,
                                 routing_key="data.zeromq.sub")
        else:
            log.debug("Not supported action")


class ZMQConnector(BaseController):
    """
    Can send and receive some information through ZMQ socket.
    """
    NAME = "zeromq"

    def __init__(self, **kwargs):
        super(ZMQConnector, self).__init__(name=ZMQConnector.NAME)
        kwargs["consumer_name"] = ZMQConnector.NAME
        self.consumer = ZMQConsumer(**kwargs)
        self.consumer.log = logging.getLogger(__name__)
        self.consumer.log.setLevel(logging.DEBUG)

    def run(self):
        self.consumer.run()
