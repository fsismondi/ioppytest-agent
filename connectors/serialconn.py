# -*- coding: utf-8 -*-

import os
import json
import serial
import logging
import threading

from connectors.base import BaseController, BaseConsumer
from utils.serial_listener import SerialListener

__version__ = (0, 0, 1)

log = logging.getLogger(__name__)

finteorp_banner = \
    """
      ______    _____       _                       
     |  ____|  |_   _|     | |                      
     | |__ ______| |  _ __ | |_ ___ _ __ ___  _ __  
     |  __|______| | | '_ \| __/ _ \ '__/ _ \| '_ \ 
     | |        _| |_| | | | ||  __/ | | (_) | |_) |
     |_|       |_____|_| |_|\__\___|_|  \___/| .__/ 
                                             | |    
                                             |_|    
    """




arrow_down = """
    ___       
   |   |              _ _       _      
   |   |             | (_)     | |         
   |   |  _   _ _ __ | |_ _ __ | | __        
   |   | | | | | '_ \| | | '_ \| |/ /      
   |   | | |_| | |_) | | | | | |   <
   |   |  \__,_| .__/|_|_|_| |_|_|\_\              
   |   |       | |           
   |   |       |_|                  
 __!   !__,   
 \       / \O 
  \     / \/| 
   \   /    | 
    \ /    / \
     Y   _/  _\ 
"""


class SerialConsumer(BaseConsumer):
    """
    AMQP helper
    """

    def __init__(self, user, password, session, server, name, consumer_name):
        super(SerialConsumer, self).__init__(user, password, session, server, name, consumer_name)
        self.dispatcher = {
            "data.serial.to_forward": self.handle_data,
        }
        self.bootstrap()
        self.message_count = 0
        self.output = ''
        self.serial_listener = None

    def bootstrap(self):
        self.serial_port = None
        try:
            self.serial_port = str(os.environ['FINTEROP_CONNECTOR_SERIAL_PORT'])
            self.baudrate = str(os.environ['FINTEROP_CONNECTOR_BAUDRATE'])

            log.info('FINTEROP_CONNECTOR_SERIAL_PORT env var imported: %s' % self.serial_port)
            log.info('FINTEROP_CONNECTOR_BAUDRATE env var imported: %s' % self.baudrate)

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


        except KeyError as e:
            logging.warning(
                'Cannot retrieve environment variables for serial connection: '
                'FINTEROP_CONNECTOR_SERIAL_PORT/FINTEROP_CONNECTOR_BAUDRATE '
                'If no sniffer/injector needed for test ignore this warning ')

    def handle_data(self, body, message):
        """
        Function that will handle serial management messages

        exchange:
        - default

        example:
        {

        }

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
            for c in body['data']:
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
                 '\n' + json.dumps(body) +
                 '\n # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # '
                 )
        message.ack()


def handle_control(self, body, message):
    msg = None

    try:
        msg = json.loads(body)
        log.debug(message)
    except ValueError as e:
        message.ack()
        log.error(e)
        log.error("Incorrect message: {0}".format(body))
        return

    if msg["_type"] in self.dispatcher.keys():
        self.dispatcher[msg["_type"]](msg)
    else:
        log.warning("Not supported action")


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
