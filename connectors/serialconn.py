"""

"""
import json
import sys
import logging
import serial
import os
import collections
from subprocess import Popen, PIPE
from .base import BaseController, BaseConsumer
from utils.serial_listener import SerialListener
import time

__version__ = (0, 0, 1)

log = logging.getLogger(__name__)


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
                'name': self.name,
                'rmq_connection': self.connection,
                'rmq_exchange': "amq.topic",
                'serial_port': self.serial_port,
                'serial_boudrate': self.baudrate,
            }
            self.serial_listener = SerialListener(**params)
            self.serial_listener.run()

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
            print('error: no serialport initiated')
            return

        # WRITE RECIEVED DATA INTO serial connector -> to SNIFFER-FWD motes -> Wireless link
        path = os.path.dirname(os.path.abspath(__file__))
        # path += "/SendCOM.py"
        # decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
        # try:
        #    bodydict = decoder.decode(body)
        # except:
        #    print ("ERROR")
        # p=Popen(['python', path, str(self.serial_port), "115200", str(bodydict['data'])], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        # print (path)
        usleep = lambda x: time.sleep(x / 1000000.0)
        ser = serial.Serial(
            port=self.serial_port,
            baudrate=self.baudrate,
            timeout=0.0)

        # inputstr=sys.argv[3]
        # ser.write(inputstr.decode('hex'))

        try:
            print(body['data'])
            # body['data'] is a byte array
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
            print(self.output)
            ser.write(self.output.decode('hex'))
            ser.flushOutput()
        except:
            print('ERROR TRYING TO WRITE IN SERIAL INTERFACE')

        print("***************** MESSAGE INJECTED : BACKEND -> WIRELESS LINK  *******************")
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
        log.debug("Not supported action")


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
        # p=Popen(['python', './ReadCOM.py', self.serial_port, "115200", str(self.name), str(self.server), str(self.session), str(self.user),str(self.password)], stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def run(self):
        self.consumer.run()

# p=Popen(['python', './ReadCOM.py', self.serial_port, "115200", str(self.name), str(self.server), str(self.session), str(self.user),str(self.password)], stdin=PIPE, stdout=PIPE, stderr=PIPE)
