# -*- coding: utf-8 -*-

"""

"""
import json
import logging
import sys
import datetime
from kombu import Producer
from connectors.base import BaseController, BaseConsumer
from utils import arrow_down, arrow_up, finterop_banner
from utils.opentun import OpenTunLinux, OpenTunMACOS

__version__ = (0, 0, 1)


class TunConsumer(BaseConsumer):
    """
    AMQP helper
    """

    def __init__(self, user, password, session, server, exchange, name, consumer_name):
        super(TunConsumer, self).__init__(user, password, session, server, exchange, name, consumer_name)
        self.dispatcher = {
            "tun.start": self.handle_start,
        }
        self.tun = None
        self.packet_count = 0

    def handle_start(self, msg):
        """
        Function that will handle tun management messages

        exchange:
        - message

        queue:
        - tun

        order:
        - start_tun

        example:
        {
            "_type": "tun.start",
            "ipv6_host": ":2",
            "ipv6_prefix": "cccc"
        }

        - stop_tun
        """
        if self.tun is not None:
            self.log.warning('Received open tun control message, but TUN already created')
            return
        else:
            self.log.info('starting tun interface')
            try:
                ipv6_host = msg.get("ipv6_host", None)
                ipv6_prefix = msg.get("ipv6_prefix", None)
                ipv6_no_forwarding = msg.get("ipv6_no_forwarding", None)
                ipv4_host = msg.get("ipv4_host", None)
                ipv4_network = msg.get("ipv4_network", None)
                ipv4_netmask = msg.get("ipv4_netmask", None)

            except AttributeError as ae:
                self.log.error(
                    'Wrong message format: {0}'.format(msg.payload)
                )
                return

            params = {
                'rmq_connection': self.connection,
                'rmq_exchange': self.exchange,
                'name': self.name,
                'ipv6_host': ipv6_host,
                'ipv6_prefix': ipv6_prefix,
                'ipv4_host': ipv4_host,
                'ipv4_network': ipv4_network,
                'ipv4_netmask': ipv4_netmask,
                'ipv6_no_forwarding': ipv6_no_forwarding
            }

            if sys.platform.startswith('win32'):
                self.log.error('Agent TunTap not yet supported for windows')
                sys.exit(1)

            elif sys.platform.startswith('linux'):
                self.log.info('Starting open tun [linux]')
                self.tun = OpenTunLinux(**params)

            elif sys.platform.startswith('darwin'):
                self.log.info('Starting open tun [darwin]')
                self.tun = OpenTunMACOS(**params)
            else:
                self.log.error('Agent TunTap not yet supported for: {0}'.format(sys.platform))
                sys.exit(1)

            msg = {
                "_type": "tun.started",
                'name': self.name,
                'ipv6_host': ipv6_host,
                'ipv6_prefix': ipv6_prefix,
                'ipv4_host': ipv4_host,
                'ipv4_network': ipv4_network,
                'ipv4_netmask': ipv4_netmask,
                'ipv6_no_forwarding': ipv6_no_forwarding,
            }
            self.log.info("Tun started. Publishing msg: %s" % json.dumps(msg))

            producer = Producer(self.connection, serializer='json')
            producer.publish(msg,
                             exchange=self.exchange,
                             routing_key='control.tun.fromAgent.%s' % self.name
                             )

    def handle_data(self, body, message):
        """

        Args:
            msg:

        Returns:

        """

        if self.tun is None:
            self.log.error("Cannot handle data packet, no tun interface yet configured")
            return

        self.packet_count += 1
        print(arrow_down)
        self.log.debug('\n* * * * * * HANDLE DATA (%s) * * * * * * *' % self.packet_count)
        self.log.debug("TIME: %s" % datetime.datetime.time(datetime.datetime.now()))
        self.log.debug(" - - - ")
        self.log.debug(("Payload", message.payload))
        self.log.debug(("Properties", message.properties))
        self.log.debug(("Headers", message.headers))
        self.log.debug(("Body", body))
        self.log.debug(("Message type (_type field)", body["_type"]))
        self.log.debug('\n* * * * * * * * * * * * * * * * * * * * * * *')

        # body is already a dict, no need to json.load it
        msg = body
        if msg["_type"] == 'packet.to_inject.raw':
            self.log.info("Message received from F-Interop. Injecting in Tun. Message count (downlink): %s"
                          % self.packet_count)

            self.tun._eventBusToTun(
                sender="F-Interop server",
                signal="tun inject",
                data=msg["data"]
            )

    def handle_control(self, body, message):
        msg = None
        try:
            msg = body
            self.log.debug(message)
            if msg["_type"]:
                self.log.debug('HANDLE CONTROL from tun processing event type: {0}'.format(msg["_type"]))
        except (ValueError, KeyError) as e:
            message.ack()
            self.log.error(e)
            self.log.error("Incorrect message: {0}".format(message.payload))
            return
        if msg["_type"] in self.dispatcher.keys():
            self.dispatcher[msg["_type"]](msg)
        else:
            self.log.debug("Not supported action")




class TunConnector(BaseController):
    """

    """

    NAME = "tun"

    def __init__(self, **kwargs):
        """

        Args:
            key: ZMQ message
        """
        super(TunConnector, self).__init__(name=TunConnector.NAME)
        self.tun = None
        kwargs["consumer_name"] = TunConnector.NAME
        self.consumer = TunConsumer(**kwargs)
        self.consumer.log = logging.getLogger(__name__)
        self.consumer.log.setLevel(logging.DEBUG)

    def run(self):
        self.consumer.run()
