# -*- coding: utf-8 -*-

"""
oficial doc on tuntap inferfaces

https://www.kernel.org/doc/Documentation/networking/tuntap.txt


from linux kernel doc:


TUN/TAP provides packet reception and transmission for user space programs.
It can be seen as a simple Point-to-Point or Ethernet device, which, instead of receiving packets from physical media,
receives them from user space program and instead of sending packets via physical media writes them to the userspace
program.

How does Virtual network device actually work ?
===============================================

Virtual network device can be viewed as a simple Point-to-Point or Ethernet device, which instead of receiving packets
from a physical media, receives them from user space program and instead of sending packets via physical media sends
them to the user space program.

Let’s say that you configured IPv6 on the tap0, then whenever the kernel sends an IPv6 packet to tap0, it is passed to
the application (VTun for example). The application encrypts, compresses and sends it to the other side over TCP or UDP.
The application on the other side decompresses and decrypts the data received and writes the packet to the TAP device,
the kernel handles the packet like it came from real physical device.
"""
import os
import json
import logging
import struct
import threading
import time
import traceback
from fcntl import ioctl
import sys

from . import arrow_down, arrow_up
from . import messages

DEFAULT_IPV6_PREFIX = 'bbbb'
DEFAULT_IPV4_NETWORK = '10.2.0.0'
DEFAULT_IPV4_NETMASK = '255.255.255.0'
DEFAULT_IPV4_BROADCAST_ADDR = '10.2.0.255'

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# ============================ defines =========================================

# insert 4 octedts ID tun for compatibility (it'll be discard)
VIRTUALTUNID = [0x00, 0x00, 0x86, 0xdd]

IFF_TUN = 0x0001
IFF_NO_PI = 0x1000
TUNSETIFF = 0x400454ca


def buf2int(buf):
    """
    Converts some consecutive bytes of a buffer into an integer.
    Big-endianness is assumed.

    :param buf:      [in] Byte array.
    """
    returnVal = 0
    for i in range(len(buf)):
        returnVal += buf[i] << (8 * (len(buf) - i - 1))
    return returnVal


# ===== formatting

def formatStringBuf(buf):
    return '({0:>2}B) {1}'.format(
        len(buf),
        '-'.join(["%02x" % ord(b) for b in buf]),
    )


def formatBuf(buf):
    """
    Format a bytelist into an easy-to-read string. For example:
    ``[0xab,0xcd,0xef,0x00] -> '(4B) ab-cd-ef-00'``
    """
    return '({0:>2}B) {1}'.format(
        len(buf),
        '-'.join(["%02x" % b for b in buf]),
    )


def formatIPv6Addr(addr):
    """
    >>> formatIPv6Addr([187, 187, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
    'bbbb:0:0:0:0:0:0:1'

    """
    # group by 2 bytes
    addr = [buf2int(addr[2 * i:2 * i + 2]) for i in range(int(len(addr) / 2))]
    return ':'.join(["%x" % b for b in addr])


def formatAddr(addr):
    return '-'.join(["%02x" % b for b in addr])


def formatThreadList():
    return '\nActive threads ({0})\n   {1}'.format(
        threading.activeCount(),
        '\n   '.join([t.name for t in threading.enumerate()]),
    )


# ===== parsing

def hex2buf(s):
    """
    Convert a string of hex caracters into a byte list. For example:
    ``'abcdef00' -> [0xab,0xcd,0xef,0x00]``

    :param s: [in] The string to convert

    :returns: A list of integers, each element in [0x00..0xff].
    """
    assert type(s) == str
    assert len(s) % 2 == 0

    returnVal = []

    for i in range(len(s) / 2):
        realIdx = i * 2
        returnVal.append(int(s[realIdx:realIdx + 2], 16))

    return returnVal


# ===== logging

def formatCriticalMessage(error):
    returnVal = []
    returnVal += ['Error:']
    returnVal += [str(error)]
    returnVal += ['\ncall stack:\n']
    returnVal += [traceback.format_exc()]
    returnVal += ['\n']
    returnVal = '\n'.join(returnVal)
    return returnVal


def formatCrashMessage(threadName, error):
    returnVal = []
    returnVal += ['\n']
    returnVal += ['======= crash in {0} ======='.format(threadName)]
    returnVal += [formatCriticalMessage(error)]
    returnVal = '\n'.join(returnVal)
    return returnVal


class TunReadThread(threading.Thread):
    """
    Thread which continously reads input from a TUN interface.

    When data is received from the interface, it calls a callback configured
    during instantiation.
    """

    ETHERNET_MTU = 1500
    IPv6_HEADER_LENGTH = 40

    def __init__(self, tunIf, callback):

        # store params
        self.tunIf = tunIf
        self.callback = callback

        # local variables
        self.goOn = True

        # initialize parent
        threading.Thread.__init__(self)

        # give this thread a name
        self.name = 'TunReadThread'

        # check if running on MacOs, in this situation tuntap driver doesnt put the 4extra bytes
        # tested with brew install Caskroom/cask/tuntap
        self.tunTapHeader = not sys.platform.startswith('darwin')

        # start myself
        self.start()

    def run(self):
        try:
            p = []

            while self.goOn:

                # wait for data
                p = os.read(self.tunIf, self.ETHERNET_MTU)

                # convert input from a string to a byte list
                p = [ord(b) for b in p]

                # debug info
                log.debug('packet captured on tun interface: {0}'.format(formatBuf(p)))

                # # ToDo clean this after proper testing
                # # if IFF_NO_PI is on, then we dont have tuntap headers
                # # remove tun ID octets
                # if self.tunTapHeader:
                #     p = p[4:]

                # make sure it's an IPv4/6 packet (i.e., starts with 0x6x)
                if (p[0] & 0xf0) != 0x60 and (p[0] & 0xf0) != 0x40:
                    log.info('this is not an IPv4/6 packet')
                    log.debug('First bytes: {0}'.format(formatBuf(p[:2])))
                    continue

                if (p[0] & 0xf0) == 0x60:
                    log.info('Got an IPv6 packet')
                elif (p[0] & 0xf0) == 0x40:
                    log.info('Got an IPv4 packet')

                # because of the nature of tun for Windows, p contains ETHERNET_MTU
                # bytes. Cut at length of IPv6 packet.
                # p = p[:self.IPv6_HEADER_LENGTH + 256 * p[4] + p[5]]

                # call the callback
                self.callback(p)

        except Exception as err:
            errMsg = formatCrashMessage(self.name, err)
            log.critical(errMsg)
            sys.exit(1)

    # ======================== public ==========================================

    def close(self):
        self.goOn = False


# TODO Create an interface class OpenTun to agregate common stuff between linux and macos

class OpenTunLinux(object):
    """
    Class which interfaces between a TUN virtual interface and an EventBus.
    """

    def __init__(self, name, rmq_connection, rmq_exchange='amq.topic', ipv6_prefix=None, ipv6_host=None,
                 ipv4_address=None):

        # RMQ setups
        self.connection = rmq_connection
        self.producer = self.connection.Producer(serializer='json')
        self.exchange = rmq_exchange

        self.name = name
        self.packet_count = 0

        if ipv6_prefix is None:
            ipv6_prefix = DEFAULT_IPV6_PREFIX
        self.ipv6_prefix = ipv6_prefix

        if ipv6_host is None:
            ipv6_host = ':1'
        self.ipv6_host = ipv6_host

        if ipv4_address is None:
            ipv4_address = '10.2.0.1'
        self.ipv4_address = ipv4_address

        self.ipv4_network = DEFAULT_IPV4_NETWORK
        self.ipv4_netmask = DEFAULT_IPV4_NETMASK

        log.debug("IP info: \n {}".format(self.get_tun_configuration()))

        # local variables
        self.tunIf = self._createTunIf()
        if self.tunIf:
            self.tunReadThread = self._createTunReadThread()
        else:
            self.tunReadThread = None

    # ======================== public ==========================================

    def get_tun_configuration(self):

        return {
            'ipv6_prefix': self.ipv6_prefix,
            'ipv6_host': self.ipv6_host,
            'ipv4_address': self.ipv4_address,
            'ipv4_network': self.ipv4_network,
            'ipv4_netmask': self.ipv4_netmask,
        }

    # def close(self):

    #     if self.tunReadThread:

    #         self.tunReadThread.close()

    #         # Send a packet to openTun interface to break out of blocking read.
    #         attempts = 0
    #         while self.tunReadThread.isAlive() and attempts < 3:
    #             attempts += 1
    #             try:
    #                 log.info('Sending UDP packet to close openTun')
    #                 sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    #                 # Destination must route through the TUN host, but not be the host itself.
    #                 # OK if host does not really exist.
    #                 dst = self.ipv6_prefix + self.ipv6_host
    #                 dst[15] += 1
    #                 # Payload and destination port are arbitrary
    #                 sock.sendto('stop', (formatIPv6Addr(dst),18004))
    #                 # Give thread some time to exit
    #                 time.sleep(0.05)
    #             except Exception as err:
    #                 log.error('Unable to send UDP to close tunReadThread: {0}'.join(err))

    # ======================== private =========================================

    def _getNetworkPrefix_notif(self, sender, signal, data):
        return self.ipv6_prefix

    def _createTunIf(self):
        """
        Open a TUN/TAP interface and switch it to TUN mode.

        :returns: The handler of the interface, which can be used for later
            read/write operations.
        """

        try:
            # =====
            log.info("opening tun interface")
            returnVal = os.open("/dev/net/tun", os.O_RDWR)
            ifs = ioctl(returnVal, TUNSETIFF, struct.pack("16sH", "tun%d", IFF_TUN | IFF_NO_PI))
            self.ifname = ifs[:16].strip("\x00")

            # =====
            log.info('configuring IPv4/6 address...')

            # delete any : character in the host string (old API used to define those with that char)
            self.ipv6_host = self.ipv6_host.replace(":", "")
            v = list()
            # v.append(os.system('ip tuntap add dev ' + self.ifname + ' mode tun user root'))
            v.append(os.system('ip link set ' + self.ifname + ' up'))
            v.append(os.system('ip addr add dev tun0 {}/24'.format(self.ipv4_address)))
            v.append(os.system('ip route add {0}/24 dev {1}'.format(self.ipv4_address, self.ifname)))
            v.append(os.system('ip -6 addr add ' + self.ipv6_prefix + '::' + self.ipv6_host + '/64 dev ' + self.ifname))
            v.append(os.system('ip -6 addr add fe80::' + self.ipv6_host + '/64 dev ' + self.ifname))

            log.info('Network configs error codes: {}'.format(v))

            # =====

            log.info('\ncreated following virtual interface:')
            log.info('-' * 72)
            os.system('ip addr show ' + self.ifname)
            log.info('-' * 72)
            log.info('\n IPv4 update routing table:')
            os.system('ip route show')
            log.info('-' * 72)
            log.info('\n IPv6 update routing table:')
            os.system('ip -6 route show')
            log.info('-' * 72)
            # =====

        except IOError as err:
            # happens when not root
            log.error('WARNING: could not created tun interface. Are you root? ({0})'.format(err))
            returnVal = None

        return returnVal

    def _createTunReadThread(self):
        """
        Creates and starts the thread to read messages arriving from the
        TUN interface.
        """
        return TunReadThread(
            self.tunIf,
            self._tunToEventBus
        )

    def _tunToEventBus(self, data):
        """
        Called when receiving data from the TUN interface.

        This function forwards the data to the the EventBus.
        """

        routing_key = messages.MsgPacketSniffedRaw.routing_key.replace('*', self.name)
        log.debug("Pushing message to topic: %s" % routing_key)

        self.packet_count += 1
        log.info("Messaged captured in tun. Pushing message to testing tool. Message count (uplink): %s"
                 % self.packet_count)

        # dispatch to EventBus
        m = messages.MsgPacketSniffedRaw(
            interface_name=self.ifname,
            timestamp=time.time(),
            data=data
        )
        print(arrow_up)
        log.info('\n # # # # # # # # # # # # OPEN TUN # # # # # # # # # # # # ' +
                 '\n packet TUN interface -> EventBus' +
                 '\n' + m.to_json() +
                 '\n # # # # # # # # # # # # # # # # # # # # # # # # # # # # #'
                 )
        # do not re-encode on json, producer does serialization
        self.producer.publish(m.to_dict(),
                              exchange=self.exchange,
                              routing_key=routing_key)

    def _eventBusToTun(self, sender, signal, data):
        """
        Called when receiving data from the EventBus.

        This function forwards the data to the the TUN interface.
        """

        # abort if not tun interface
        if not self.tunIf:
            return

        # convert data to string
        data = ''.join([chr(b) for b in data])

        try:
            # write over tuntap interface
            out = os.write(self.tunIf, data)
            if log.isEnabledFor(logging.DEBUG):
                log.debug("data dispatched to tun correctly, event: {0}, sender: {1}".format(signal, sender))
                log.debug("writing in tunnel, data {0}".format(formatStringBuf(data)))
        except Exception as err:
            errMsg = formatCriticalMessage(err)
            log.critical(errMsg)


class OpenTunMACOS(object):
    '''
    Class which interfaces between a TUN virtual interface and an EventBus.
    '''

    def __init__(self, name, rmq_connection, rmq_exchange='amq.topic', ipv6_prefix=None, ipv6_host=None,
                 ipv4_address=None):

        # RMQ setups
        self.connection = rmq_connection
        self.producer = self.connection.Producer(serializer='json')
        self.exchange = rmq_exchange

        self.name = name
        self.tun_name = ''
        self.packet_count = 0

        if ipv6_prefix is None:
            # self.ipv6_prefix = [0xbb, 0xbb, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            ipv6_prefix = DEFAULT_IPV6_PREFIX
        self.ipv6_prefix = ipv6_prefix

        if ipv6_host is None:
            # self.ipv6_host = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01]
            ipv6_host = '1'
        self.ipv6_host = ipv6_host

        if ipv4_address is None:
            ipv4_address = '10.2.0.1'
        self.ipv4_address = ipv4_address

        self.ipv4_network = DEFAULT_IPV4_NETWORK
        self.ipv4_netmask = DEFAULT_IPV4_NETMASK

        log.debug("IP info: \n {}".format(self.get_tun_configuration()))

        # local variables
        self.tunIf = self._createTunIf()
        if self.tunIf:
            self.tunReadThread = self._createTunReadThread()
        else:
            self.tunReadThread = None

    # ======================== public ==========================================

    def get_tun_configuration(self):

        return {
            'ipv6_prefix': self.ipv6_prefix,
            'ipv6_host': self.ipv6_host,
            'ipv4_address': self.ipv4_address,
            'ipv4_network': self.ipv4_network,
            'ipv4_netmask': self.ipv4_netmask,
        }

    # ======================== private =========================================

    def _getNetworkPrefix_notif(self, sender, signal, data):
        return self.ipv6_prefix

    def _createTunIf(self):
        '''
        Open a TUN/TAP interface and switch it to TUN mode.

        :returns: The handler of the interface, which can be used for later
            read/write operations.
        '''
        # =====

        # import random
        # TODO test concurrency problems with MacOs drivers when launching two agents in same PC
        # random_time = 1 + (random.randint(0, 1000) / 1000)
        # log.debug('waiting {rt} before starting the tun'.format(rt=random_time))
        # time.sleep(random_time)

        log.info("opening tun interface")
        tun_counter = 0
        while tun_counter < 16:
            try:
                self.ifname = 'tun{0}'.format(tun_counter)
                f = os.open("/dev/{0}".format(self.ifname), os.O_RDWR)
                break
            except OSError:
                tun_counter += 1

        if tun_counter == 16:
            raise OSError('TUN device not found: check if it exists or if it is busy.'
                          ' TunTap driver installed on MacOs?'
                          ' Running as root?')
        else:

            # =====
            log.info('configuring tun IPv4/6 address...')

            # delete starting ":"
            self.ipv6_host = self.ipv6_host.replace(":", "")

            v = list()
            v.append(os.system(
                'ifconfig {0} inet6 {1}::{2} prefixlen 64'.format(self.ifname, self.ipv6_prefix, self.ipv6_host)))
            v.append(os.system('ifconfig {0} inet6 fe80::{1} prefixlen 64 add'.format(self.ifname, self.ipv6_host)))

            v.append(os.system('ifconfig {0} inet {1} netmask {2} broadcast {3}'.format(
                self.ifname,
                self.ipv4_address,
                self.ipv4_netmask,
                DEFAULT_IPV4_BROADCAST_ADDR
            )))
            v.append(os.system('route -n add {0}/24 -interface {1}'.format(self.ipv4_address, self.ifname)))

            log.info('Network configs error codes: {}'.format(v))

            # =====
            log.info('\ncreated following virtual interface:')
            print('-' * 72)
            os.system('ifconfig {0}'.format(self.ifname))
            print('-' * 72)
            log.info('\nupdate routing table:')
            os.system('netstat -nr')
            print('-' * 72)
            # =====

            return f

    def _createTunReadThread(self):
        '''
        Creates and starts the thread to read messages arriving from the
        TUN interface.
        '''
        return TunReadThread(
            self.tunIf,
            self._tunToEventBus
        )

    def _tunToEventBus(self, data):
        """
        Called when receiving data from the TUN interface.

        This function forwards the data to the the EventBus.
        """

        routing_key = messages.MsgPacketSniffedRaw.routing_key.replace('*', self.name)
        log.debug("Pushing message to topic: %s" % routing_key)

        self.packet_count += 1
        log.info("Messaged captured in tun. Pushing message to testing tool. Message count (uplink): %s"
                 % self.packet_count)

        # dispatch to EventBus
        m = messages.MsgPacketSniffedRaw(
            interface_name=self.ifname,
            timestamp=time.time(),
            data=data
        )
        print(arrow_up)
        log.info('\n # # # # # # # # # # # # OPEN TUN # # # # # # # # # # # # ' +
                 '\n packet TUN interface -> EventBus' +
                 '\n' + m.to_json() +
                 '\n # # # # # # # # # # # # # # # # # # # # # # # # # # # # #'
                 )
        # do not re-encode on json, producer does serialization
        self.producer.publish(m.to_dict(),
                              exchange=self.exchange,
                              routing_key=routing_key)

    def _eventBusToTun(self, sender, signal, data):
        """
        Called when receiving data from the EventBus.

        This function forwards the data to the the TUN interface.
        """

        # abort if not tun interface
        if not self.tunIf:
            return

        # add tun header
        # data = VIRTUALTUNID + data

        # import binascii
        # stri = ""
        # for i in data:
        #     if type(i)==int:
        #         #stri += str(i)
        #         stri += binascii.hexlify(str(i))
        #     else:
        #         #stri += i.decode('utf-8')
        #         stri += binascii.hexlify(i.decode('utf-8'))

        log.info('\n # # # # # # # # # # # # OPEN TUN # # # # # # # # # # # # ' +
                 '\n packet EventBus -> TUN' +
                 '\n' + json.dumps(data) +
                 '\n # # # # # # # # # # # # # # # # # # # # # # # # # # # # #'
                 )
        # convert data to string
        data = ''.join([chr(b) for b in data])

        try:
            # write over tuntap interface
            os.write(self.tunIf, data)
            if log.isEnabledFor(logging.DEBUG):
                log.debug("data dispatched to tun correctly, event: {0}, sender: {1}".format(signal, sender))
        except Exception as err:
            errMsg = formatCriticalMessage(err)
            log.critical(errMsg)

            # ======================== helpers =========================================
