# -*- coding: utf-8 -*-

"""

"""
import json
import logging
import sys
import datetime
from kombu import Producer

from .base import BaseController, BaseConsumer
from ..utils.opentun import OpenTunLinux, OpenTunMACOS
from ..utils import arrow_up, arrow_down
from ..utils import messages


class TunConsumer(BaseConsumer):
    """
    Tun interface consumer:
        - creates tunnel interface (RAW_IP)
        - injects IPv6 packets coming from event bus into tun interface
        - captures and forwards packets from tun interface to event bus
    """

    def __init__(self, user, password, session, server, exchange, name, consumer_name,
                 force_bootstrap, ipv6_host, ipv6_prefix,
                 re_route_packets_prefix, re_route_packets_host, re_route_packets_if):

        self.dispatcher = {
            messages.MsgAgentTunStart: self.handle_start,
            messages.MsgPacketInjectRaw: self.handle_raw_packet_to_inject,
        }
        self.tun = None
        self.packet_count = 0

        subscriptions = [
            messages.MsgAgentTunStart.routing_key.replace('*', name),  # default rkey is "toAgent.*.ip.tun.start"
            messages.MsgPacketInjectRaw.routing_key.replace('*', name)
        ]

        super(TunConsumer, self).__init__(user, password, session, server, exchange, name, consumer_name, subscriptions)

        if force_bootstrap:
            self.handle_start(
                messages.MsgAgentTunStart(
                    name=name,
                    ipv6_host=ipv6_host,
                    ipv6_prefix=ipv6_prefix,
                    ipv6_no_forwarding=False if re_route_packets_prefix and re_route_packets_host else True,
                    ipv4_host=None,
                    ipv4_network=None,
                    ipv4_netmask=None,
                    re_route_packets_if=re_route_packets_if,
                    re_route_packets_prefix=re_route_packets_prefix,
                    re_route_packets_host=re_route_packets_host
                )
            )

    def _on_message(self, message):
        msg_type = type(message)
        assert msg_type in self.dispatcher.keys(), 'Event message couldnt be dispatched %s' % repr(message)
        self.log.debug(
            "Consumer specialized handler <{consumer_name}> got: {message}".format(
                consumer_name=self.consumer_name,
                message=repr(message)
            )
        )
        self.dispatcher[msg_type](message)

    def _publish_agent_tun_started_message(self):
        assert self.tun is not None

        def errback(exc, interval):
            self.log.error('Error: %r', exc, exc_info=1)
            self.log.info('Retry in %s seconds.', interval)

        # get config from tun
        conf_params = self.tun.get_tun_configuration()
        conf_params.update({'name': self.name})

        # publish message in event bus
        msg = messages.MsgAgentTunStarted(**conf_params)
        self.log.debug('Publishing %s' % repr(msg))

        producer = Producer(self.connection, serializer='json')
        publish = self.connection.ensure(producer, producer.publish, errback=errback, max_retries=3)

        publish(
            body=msg.to_dict(),
            exchange=self.exchange,
            routing_key='fromAgent.{0}.ip.tun.started'.format(self.name)
        )

    def handle_start(self, msg):
        """
        Function that will handle tun start event emitted coming from backend
        """
        if self.tun is not None:
            self.log.warning('Received open tun control message, but TUN already created')

        else:
            self.log.info('starting tun interface')
            try:
                ipv6_host = msg.ipv6_host
                ipv6_prefix = msg.ipv6_prefix
                ipv6_no_forwarding = msg.ipv6_no_forwarding
                ipv4_host = msg.ipv4_host
                ipv4_network = msg.ipv4_network
                ipv4_netmask = msg.ipv4_netmask
                re_route_packets_if = msg.re_route_packets_if
                re_route_packets_prefix = msg.re_route_packets_prefix
                re_route_packets_host = msg.re_route_packets_host

            except AttributeError as ae:
                self.log.error(
                    'Wrong message format: {0}'.format(repr(msg))
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
                'ipv6_no_forwarding': ipv6_no_forwarding,
                're_route_packets_if': re_route_packets_if,
                're_route_packets_prefix': re_route_packets_prefix,
                're_route_packets_host': re_route_packets_host
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

        self._publish_agent_tun_started_message()

    def handle_raw_packet_to_inject(self, message):
        """
        Handles data messages to be injected in network interface
        """
        if self.tun is None:
            self.log.error("Cannot handle data packet, no tun interface yet configured")
            return

        self.packet_count += 1

        self.log.info("Message received from testing tool. Injecting in Tun. Message count (downlink): %s"
                      % self.packet_count)

        print(arrow_down)
        self.log.info('\n # # # # # # # # # # # # OPEN TUN # # # # # # # # # # # # ' +
                      '\n data packet EventBus -> TUN interface' +
                      '\n' + message.to_json() +
                      '\n # # # # # # # # # # # # # # # # # # # # # # # # # # # # #'
                      )

        self.tun._eventBusToTun(
            sender="Testing Tool",
            signal="tun inject",
            data=message.data
        )


class TunConnector(BaseController):
    """

    """

    NAME = "tun"

    def __init__(self, **kwargs):
        super(TunConnector, self).__init__(name=TunConnector.NAME)
        self.tun = None
        kwargs["consumer_name"] = TunConnector.NAME
        self.consumer = TunConsumer(**kwargs)
        self.consumer.log = logging.getLogger(__name__)
        self.consumer.log.setLevel(logging.DEBUG)

    def run(self):
        self.consumer.run()
