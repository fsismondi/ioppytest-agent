# -*- coding: utf-8 -*-
import sys
import os
import json
import serial
import logging
import threading

from .base import BaseController, BaseConsumer
from ..utils import messages
from ..utils import arrow_down, arrow_up
from ..utils.serial_listener import SerialListener

__version__ = (0, 1, 0)

log = logging.getLogger(__name__)


class SerialConsumer(BaseConsumer):
    """
    Serial interface consumer:
        - Set up process which communicates with serial interface of mote through USB port
        - transmits in and out 802.15.4 packet messages
    """

    def __init__(self, user, password, session, server, exchange, name, consumer_name):

        self.dispatcher = {
            messages.MsgPacketInjectRaw: self.handle_data,
        }

        subscriptions = [
            messages.MsgPacketInjectRaw.routing_key.replace('*', name).replace('ip.tun', '802154.serial'),
        ]

        super(SerialConsumer, self).__init__(user, password, session, server, exchange, name, consumer_name,
                                             subscriptions)
        self.message_count = 0
        self.output = ''
        self.serial_listener = None
        self.bootstrap()

    def bootstrap(self):
        self.serial_port = None
        try:
            self.serial_port = str(os.environ['FINTEROP_CONNECTOR_SERIAL_PORT'])
            self.baudrate = str(os.environ['FINTEROP_CONNECTOR_BAUDRATE'])

            log.info('FINTEROP_CONNECTOR_SERIAL_PORT env var imported: %s' % self.serial_port)
            log.info('FINTEROP_CONNECTOR_BAUDRATE env var imported: %s' % self.baudrate)

        except KeyError as e:
            logging.error(
                'Cannot retrieve environment variables for serial connection: '
                'FINTEROP_CONNECTOR_SERIAL_PORT/FINTEROP_CONNECTOR_BAUDRATE '
                'please make sure these have been exported before starging agent'
            )
            sys.exit(1)

        try:
            # open a subprocess to listen the serialport
            params = {
                'agent_name': self.name,
                'rmq_connection': self.connection,
                'rmq_exchange': "amq.topic",
                'serial_port': self.serial_port,
                'serial_boudrate': self.baudrate,
            }
            serial_listener = SerialListener(**params)
            serial_listener_th = threading.Thread(target=serial_listener.run, args=())
            serial_listener_th.daemon = True
            serial_listener_th.start()

        except Exception as e:
            log.error(e)
            sys.exit(1)

        log.info('%s bootstraped.' % self.name)

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

    def handle_data(self, message):
        """
        Forwards data packets from AMQP BUS to serial interface

        """
        if self.serial_port is None:
            log.error('No serial port initiated')
            return

        ser = serial.Serial(
            port=self.serial_port,
            baudrate=self.baudrate,
            timeout=0.0)

        try:
            self.output = 'c0'
            for c in message.data:
                if format(c, '02x') == 'c0':
                    # endslip
                    self.output += 'db'
                    self.output += 'dc'
                elif format(c, '02x') == 'db':
                    # esc
                    self.output += 'db'
                    self.output += 'dd'
                else:
                    self.output += format(c, '02x')
            self.output += 'c0'
            ser.write(self.output.decode('hex'))
            ser.flushOutput()
        except:
            log.error('Error while tring to write serial interface')

        print(arrow_down)
        log.info('\n # # # # # # # # # # # # SERIAL INTERFACE # # # # # # # # # # # # ' +
                 '\n data packet EventBus -> Serial' +
                 '\n' + message.to_json() +
                 '\n # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # '
                 )


class SerialConnector(BaseController):
    """

    """
    NAME = "serial"

    def __init__(self, **kwargs):
        """

        Args:
            key: Serial message
        """
        super(SerialConnector, self).__init__(name=SerialConnector.NAME)
        self.serial = None
        kwargs["consumer_name"] = SerialConnector.NAME
        self.consumer = SerialConsumer(**kwargs)
        self.consumer.log = logging.getLogger(__name__)
        self.consumer.log.setLevel(logging.DEBUG)

    def run(self):
        self.consumer.run()
