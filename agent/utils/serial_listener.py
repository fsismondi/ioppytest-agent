# -*- coding: utf-8 -*-

import serial
import logging
import sys

from kombu import Exchange
from ..utils import messages

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

arrow_down = """
    ___       
   |   |       
   |   |       _                     _ _       _    
   |   |      | |                   | (_)     | |   
   |   |    __| | _____      ___ __ | |_ _ __ | | __
   |   |   / _` |/ _ \\ \\ /\\ / / '_ \\| | | '_ '\\| |/ /
   |   |  | (_| | (_) \\ V  V /| | | | | | | | |   < 
   |   |   \\__,_|\\___/ \\_/\\_/ |_| |_|_|_|_| |_|_|\_\\
   |   | 
 __!   !__,
 \\       / \O
  \\     / \/|
   \\   /    |
    \\ /    / \\
     Y   _/  _\\
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

        log.info("opening serial reader...")
        try:
            self.ser = serial.Serial(port=self.dev,
                                     baudrate=int(self.br),
                                     timeout=0.001
                                     )
        except serial.serialutil.SerialException as e:
            log.error(e)
            log.error('Does dev %s exist?' % serial_port)
            sys.exit(1)

        try:
            self.ser.flushInput()
        except Exception as e:
            log.error(e)

        self.message_read_count = 0

        # notify interface is opened
        m = messages.MsgAgentSerialStarted(
            name=self.agent_name,
            port=self.dev,
            boudrate=self.br
        )

        self.producer.publish(
            m.to_dict(),
            exchange=self.exchange,
            routing_key=messages.MsgAgentSerialStarted.routing_key.replace('*', self.agent_name)
        )

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
        else:
            log.debug("Rubbish message dropped..")

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

        m = messages.MsgPacketSniffedRaw(
            interface_name='serial',
            data=self.convert_bytearray_to_intarray(bytearray.fromhex(data)),
            data_slip=self.convert_bytearray_to_intarray(bytearray.fromhex(data_slip)),
        )

        self.frame_slip = ''

        self.producer.publish(
            m.to_dict(),
            exchange=self.exchange,
            routing_key="fromAgent.{agent_name}.802154.serial.packet.raw".format(agent_name=self.agent_name)
        )
        print(arrow_up)
        log.info('\n # # # # # # # # # # # # SERIAL INTERFACE # # # # # # # # # # # # ' +
                 '\n data packet Serial -> EventBus' +
                 '\n' + m.to_json() +
                 '\n # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # '
                 )

    def run(self):
        log.info("starting serial reader thread...")
        try:
            while not self.closed():
                numbytes = self.ser.inWaiting()
                if numbytes > 0:
                    output = self.ser.read(numbytes)  # read output
                    self.recv_chars(output)
        except Exception as e:
            log.error('Error found while processing received data stream in serial: %s' % str(e))
            sys.exit(1)
