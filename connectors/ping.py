"""
Create ICMP packets to test if all nodes are up
"""
import json

__version__ = (0, 0, 1)

import logging

from .base import BaseController, BaseConsumer
import subprocess


class PingConsumer(BaseConsumer):
    """
    AMQP helper
    """

    def __init__(self, user, password, session, server, name, consumer_name):
        super(PingConsumer, self).__init__(user, password, session, server, name, consumer_name)

    def handle_control(self, body, message):
        """

        Args:
            body:
            message:

        Returns:

        """
        required_keys = {"host"}
        msg = None
        try:
            msg = json.loads(body)
            self.log.debug(message)
        except ValueError as e:
            message.ack()
            self.log.error(e)
            self.log.error("Incorrect message: {0}".format(body))

        if msg is not None:
            present_keys = set(msg.keys())
            if not present_keys.issuperset(required_keys):
                self.log("Error you need those keys: %s" % required_keys)
            else:
                # Default version is ping
                version = {"IPv6": "ping6", "IPv4": "ping"}
                executable = version.get(msg["version"], "ping")

                # default packet count is 1
                count_option = msg.get("count", 1)

                # network interface, default is None
                interface_option = msg.get("interface", "")

                # run the ping
                command = [executable, msg["host"], "-c", str(count_option)]
                self.log.info("command launched: %s" % command)
                p = subprocess.call(command)

                self.log.info("result: %s" % p)


class PingConnector(BaseController):
    NAME = "ping"

    def __init__(self, **kwargs):
        super(PingConnector, self).__init__(name=PingConnector.NAME)
        kwargs["consumer_name"] = PingConnector.NAME
        self.consumer = PingConsumer(**kwargs)
        self.consumer.log = logging.getLogger(__name__)
        self.consumer.log.setLevel(logging.DEBUG)

    def run(self):
        self.consumer.run()
