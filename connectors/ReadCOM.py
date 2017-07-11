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
        self.length = 0
        self.amqp_exchange = str(os.environ['AMQP_EXCHANGE'])
        self.ser = serial.Serial(
            port=dev, \
            baudrate=int(br), \
            timeout=0.001)

        self.mrkey = "data.serial.fromAgent." + name

        #        if name == "agent1":
        #            self.mrkey += "agent2"
        #        else:
        #            self.mrkey += "agent1"

        credentials = pika.PlainCredentials(user, passwd)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=server, \
            virtual_host=session, \
            credentials=credentials))
        self.ch = connection.channel()

    #		thread=threading.Thread(target=self.run,args=())
    #		thread.daemon=True
    #		thread.start()

    def recv_chars(self, chars):
        if chars:
            for c in chars:
                if c.encode('hex') == 'c0':
                    if self.start_frame == 0:
                        self.start_frame = 1
                        self.frame = c
                        self.length = 0
                    if self.start_frame == 1 and self.length > 0:
                        self.start_frame = 0
                        self.frame += c
                        self.send_amqp(self.frame)
                else:
                    if self.start_frame == 1:
                        self.length += 1
                        self.frame += c

    def send_amqp(self, data):
        print(data.encode('hex'))
        body = OrderedDict()
        body['_type'] = 'data.serial.to_forward'
        body['data'] = data.encode('hex')
        print
        self.mrkey
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
