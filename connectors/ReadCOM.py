import sys
import pika
import json
import serial
import os
import time
from collections import OrderedDict
from binascii import unhexlify
import time


# import myqueues
# ser = serial.Serial(
#   port=sys.argv[1],\
#   baudrate=int(sys.argv[2]),\
#   timeout=0.001)
# print (sys.argv[1])
# print (sys.argv[2])
# print (sys.argv[3])
STATE_OK = 0
STATE_ESC = 1
STATE_RUBBISH = 2
SLIP_END = 'c0'
SLIP_ESC = 'db'
SLIP_ESC_END = 'dc'
SLIP_ESC_ESC = 'dd'
class ReadCOM(object):

    def __init__(self, dev, br, name, server, session, user, passwd):
        self.dev = dev
        self.br = br
        self.name = name
        self.server = server
        self.session = session
        self.user = user
        self.passwd = passwd
        self.frame = ''
        self.start_frame = 0
        self.amqp_exchange = str(os.environ['AMQP_EXCHANGE'])
        self.state=STATE_RUBBISH
        self.ser = serial.Serial(
            port=dev, \
            baudrate=int(br), \
            timeout=0.001)

        self.mrkey = "data.serial.fromAgent." + name

        # if name == "coap_server_agent":
        #     self.mrkey += "coap_client_client"
        # elif name == "coap_client_agent":
        #     self.mrkey += "coap_server_agent"

        credentials = pika.PlainCredentials(user, passwd)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=server, \
            virtual_host=session, \
            credentials=credentials))
        self.ch = connection.channel()

    #		thread=threading.Thread(target=self.run,args=())
    #		thread.daemon=True
    #		thread.start()
    def state_rubbish(self, data):
        if data.encode('hex') == SLIP_END:
            self.state = STATE_OK

    def state_esc(self, data):
        if data.encode('hex') != SLIP_ESC_END and data.encode('hex') != SLIP_ESC_ESC:
            self.state = STATE_RUBBISH
            self.start_frame = 0
            self.frame = ''
        else:
            self.state = STATE_OK

    def state_ok(self,data):
        if data.encode('hex') == SLIP_ESC:
            self.state=STATE_ESC
        else:
            if data.encode('hex') == SLIP_END:
                if self.start_frame == 0:
                #start frame
                    self.start_frame = 1
                    self.frame = ''
                else:
                #end frame
                    self.start_frame = 0
                    self.send_amqp(self.frame)
                    self.state = STATE_RUBBISH
            else:
                if data.encode('hex') == SLIP_ESC_ESC:
                    self.frame += "\xDB"
                if data.encode('hex') == SLIP_ESC_END:
                    self.frame += "\xC0"
                else:
                    self.frame += data

    def recv_chars(self, chars):
        if chars:
            for c in chars:
                if self.state == STATE_RUBBISH:
                    self.state_rubbish(c)
                if self.state == STATE_ESC:
                    self.state_esc(c)
                if self.state == STATE_OK:
                    self.state_ok(c)




    def send_amqp(self, data):
        print(data.encode('hex'))
        body = OrderedDict()
        body['_type'] = 'data.serial.to_forward'
        body['data'] = data.encode('hex')
        print self.mrkey
        self.ch.basic_publish(exchange=self.amqp_exchange, \
                              routing_key=self.mrkey, \
                              body=json.dumps(body), )

    def run(self):
        while True:
            numbytes = self.ser.inWaiting()
            if numbytes > 0:
                output = self.ser.read(numbytes)  # read output
                self.recv_chars(output)


# p=ReadCOM('/dev/ttyUSB0','115200','agent2','f-interop.rennes.inria.fr','session01','paul','iamthewalrus')
p = ReadCOM(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
while True:
    numbytes = p.ser.inWaiting()
    if numbytes > 0:
        output = p.ser.read(numbytes)  # read output
        p.recv_chars(output)

# print (sys.argv[1])
# print (int(sys.argv[2]))
# print (sys.argv[3])
# print (sys.argv[4])
# print (sys.argv[5])
# print (sys.argv[6])
# print (sys.argv[7])
