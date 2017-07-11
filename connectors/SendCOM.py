import sys
import serial
import time
usleep = lambda x: time.sleep(x/1000000.0)
ser=serial.Serial(
	port=sys.argv[1],\
	baudrate=int(sys.argv[2]),\
	timeout=0.0)
inputstr=sys.argv[3]
ser.write(inputstr.decode('hex'))
usleep(300000)


