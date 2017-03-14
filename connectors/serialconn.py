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
from threading import Thread
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
        #        thread = Thread(target=self.bootstrap(), args=())
        #	thread.daemon = True
        #	thread.start()
        self.bootstrap()
        self.message_count = 0

    #	print ("it ok")


    def bootstrap(self):
        self.serial_port = None

        try:
            self.serial_port = str(os.environ['FINTEROP_CONNECTOR_SERIAL_PORT'])
            log.info('FINTEROP_CONNECTOR_SERIAL_PORT env var imported: %s' % self.serial_port)
            # open a subprocess to listen the serialport
            path = os.path.dirname(os.path.abspath(__file__))
            path += "/ReadCOM.py"
            print(path)
            p = Popen(['python', path, str(self.serial_port), "115200", str(self.name), str(self.server),
                       str(self.session), str(self.user), str(self.password)], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        except KeyError as e:
            logging.warning(
                    'Cannot retrieve environment variables for serial connection: '
                    'FINTEROP_CONNECTOR_SERIAL_PORT'
                    'if no sniffer/injector needed for test ignore this warning')

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
        decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
        bodydict = decoder.decode(body)
        # p=Popen(['python', path, str(self.serial_port), "115200", str(bodydict['data'])], stdin=PIPE, stdout=PIPE, stderr=PIPE)

        # print (path)

        usleep = lambda x: time.sleep(x / 1000000.0)
        ser = serial.Serial(
                port=self.serial_port,
                baudrate=115200,
                timeout=0.0)

        # inputstr=sys.argv[3]
        # ser.write(inputstr.decode('hex'))

        try:
            ser.write(bodydict['data'].decode('hex'))
        except:
            print('ERROR TRYING TO WRITE IN SERIAL INTERFACE')
        usleep(300000)

        # p.wait()
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
