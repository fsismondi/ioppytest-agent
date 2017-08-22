# -*- coding: utf-8 -*-

import json
import serial
import logging
import threading
import time
import signal
import sys


from kombu import Exchange
from collections import OrderedDict

STATE_OK = 0
STATE_ESC = 1
STATE_RUBBISH = 2
SLIP_END = 'c0'
SLIP_ESC = 'db'
SLIP_ESC_END = 'dc'
SLIP_ESC_ESC = 'dd'

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


arrow_up = """
      _
     / \\
    /   \\
   /     \\
  /       \\
 /__     __\\   
    |   |              _ _       _      
    |   |             | (_)     | |         
    |   |  _   _ _ __ | |_ _ __ | | __        
    |   | | | | | '_ \| | | '_ \\| |/ /      
    |   | | |_| | |_) | | | | | |   <
    |   |  \__,_| .__/|_|_|_| |_|_|\_\\              
    |   |       | |           
    |   |       |_|                  
    !___!   
   \\  O  / 
    \\/|\/ 
      | 
     / \\
   _/   \\ _

"""


class SerialListener(object):
    def __init__(self, agent_name, rmq_connection, rmq_exchange="amq.topic", serial_port='/dev/ttyUSB0',
                 serial_boudrate='460800'):
        # give this thread a name
        self.name = 'SerialListener'
        self._stop = False

        # RMQ setups
        self.connection = rmq_connection
        self.producer = self.connection.Producer(serializer='json')
        self.exchange = Exchange(rmq_exchange, type="topic", durable=True)

        # serial interface Listener config
        self.dev = serial_port
        self.br = serial_boudrate
        self.agent_name = agent_name
        self.frame = ''
        self.start_frame = 0
        self.state = STATE_OK
        self.frame_slip = ''

        log.info("opening serial reader..")
        self.ser = serial.Serial(port=self.dev,
                                 baudrate=int(self.br),
                                 timeout=0.001
                                 )
        self.ser.flushInput()

        self.mrkey = "data.serial.fromAgent.%s" % self.agent_name
        self.message_read_count = 0

    def close(self):
        self._stop = True

    def closed(self):
        return self._stop

    def state_rubbish(self, data):
        if data.encode('hex') == SLIP_END:
            self.state = STATE_OK
            self.start_frame = 0
            self.frame = ''
            self.frame_slip = ''

    def state_esc(self, data):
        if data.encode('hex') != SLIP_ESC_END and data.encode('hex') != SLIP_ESC_ESC:
            self.state = STATE_RUBBISH
            self.start_frame = 0
            self.frame = ''
        else:
            self.state = STATE_OK
            if self.start_frame == 1:
                if data.encode('hex') == SLIP_ESC_ESC:
                    self.frame += SLIP_ESC
                elif data.encode('hex') == SLIP_ESC_END:
                    self.frame += SLIP_END

    def state_ok(self, data):
        if data.encode('hex') == SLIP_ESC:
            self.state = STATE_ESC
        else:
            if data.encode('hex') == SLIP_END:
                if self.start_frame == 0:
                    # start frame
                    self.start_frame = 1
                    self.frame = ''
                else:
                    # end frame
                    self.start_frame = 0
                    self.send_amqp(self.frame, self.frame_slip)
                    self.state = STATE_OK
            else:
                if self.start_frame == 1:
                    self.frame += data.encode('hex')
                else:
                    self.state = STATE_RUBBISH

    def recv_chars(self, chars):
        self.message_read_count += 1
        log.debug("Message received in serial interface. Count: %s" % self.message_read_count)
        if chars:
            for c in chars:
                if self.state == STATE_RUBBISH:
                    self.state_rubbish(c)
                    continue
                self.frame_slip += c.encode('hex')
                if self.state == STATE_ESC:
                    self.state_esc(c)
                    continue
                if self.state == STATE_OK:
                    self.state_ok(c)

    def convert_bytearray_to_intarray(self, ba):
        ia = []
        for e in ba:
            ia.append(e)
        return ia

    def send_amqp(self, data, data_slip):
        body = OrderedDict()

        body['_type'] = 'packet.sniffed.raw'
        body['interface_name'] = 'serial'
        body['data'] = self.convert_bytearray_to_intarray(bytearray.fromhex(data))
        body['data_slip'] = self.convert_bytearray_to_intarray(bytearray.fromhex(data_slip))
        self.frame_slip = ''

        self.producer.publish(body,
                              exchange=self.exchange,
                              routing_key=self.mrkey)
        print(arrow_up)
        log.info('\n # # # # # # # # # # # # SERIAL INTERFACE # # # # # # # # # # # # ' +
                 '\n data packet Serial -> EventBus' +
                 '\n' + json.dumps(body) +
                 '\n # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # '
                 )

    def run(self):
        log.info("starting serial reader thread..")
        try:
            while not self.closed():
                numbytes = self.ser.inWaiting()
                if numbytes > 0:
                    output = self.ser.read(numbytes)  # read output
                    self.recv_chars(output)
        except:
            sys.exit(1)
