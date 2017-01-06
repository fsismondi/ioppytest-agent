"""

"""
import json
import logging
import sys

from kombu import Connection
from kombu import Queue

from connectors.base import BaseController, BaseConsumer
from utils.opentun import OpenTunLinux, OpenTunMACOS

__version__ = (0, 0, 1)

log = logging.getLogger(__name__)


class TunConsumer(BaseConsumer):
    """
    AMQP helper
    """

    def __init__(self, user, password, session, server, name, consumer_name):
        super(TunConsumer, self).__init__(user, password, session, server, name, consumer_name)
        self.dispatcher = {
            "tun.start": self.handle_start,
        }


    def handle_start(self, msg):
        """
        Function that will handle tun management messages

        exchange:
        - message

        queue:
        - tun

        order:
        - start_tun

        example:
        {
            "_type": "tun.start",
            "ipv6_host": ":2",
            "ipv6_prefix": "cccc"
        }

        - stop_tun
        """
        logging.info('starting tun interface')
        try:
            ipv6_host = msg.get("ipv6_host", None)
            ipv6_prefix = msg.get("ipv6_prefix", None)
            ipv4_host = msg.get("ipv4_host", None)
            ipv4_network = msg.get("ipv4_network", None)
            ipv4_netmask = msg.get("ipv4_netmask", None)
        except AttributeError as ae:
            logging.error(
                    'Wrong message format: {0}'.format(msg.payload)
            )
            return


        params = {
            'rmq_connection' : self.connection,
            'name' : self.name,
            'ipv6_host' : ipv6_host,
            'ipv6_prefix' : ipv6_prefix,
            'ipv4_host' : ipv4_host,
            'ipv4_network' : ipv4_network,
            'ipv4_netmask' : ipv4_netmask,
        }

        if sys.platform.startswith('win32'):
            log.error('Agent TunTap not yet supported for windows')
            sys.exit(1)

        elif sys.platform.startswith('linux'):
            logging.info('Starting open tun [linux]')
            self.tun = OpenTunLinux(**params)

        elif sys.platform.startswith('darwin'):
            logging.info('Starting open tun [darwin]')
            self.tun = OpenTunMACOS(**params)
        else:
            log.error('Agent TunTap not yet supported for: {0}'.format(sys.platform))
            sys.exit(1)


    def handle_data(self, body, message):
        """

        Args:
            msg:

        Returns:

        """
        self.log.debug("HANDLE DATA from tun")
        self.log.debug(("Payload", message.payload))
        self.log.debug(("Properties", message.properties))
        self.log.debug(("Headers", message.headers))
        self.log.debug(("body", message.body))

    def handle_control(self, body, message):
        msg = None
        try:
            # body is a json
            msg = json.loads(body)
            log.debug(message)
            if msg["_type"]:
                log.debug('HANDLE CONTROL from tun processing event type: {0}'.format(msg["_type"]))
        except (ValueError,KeyError) as e:
            message.ack()
            log.error(e)
            log.error("Incorrect message: {0}".format(message.payload))
            return
        if msg["_type"] in self.dispatcher.keys():
            self.dispatcher[msg["_type"]](msg)
        else:
            log.debug("Not supported action")


# elif "data" in msg.keys():
# if msg["routing_key"] == "tun.pkt" and self.tun is None:
#     log.warning("Received data packet but tun is not open. send a start_tun command")
# if msg["routing_key"] == "tun.pkt" and self.tun is not None:
#     self.tun._v6ToInternet_notif("sender", "signal", msg["data"])
# else:
#     log.info("Don't know how to handle those packets")

# def handle_control(self, body, message):

#     if msg is not None:
#         # Prefer a narrow filter to avoid having
#         sniffer_filter = "udp port 5683"

#         interface_filter = "lo"  # Listening on the local loop only
#         if "order" in msg.keys():
#             if msg["order"] == "launchSniffer":
#                 log.info("Start the sniffer")
#                 # output_path = str(uuid.uuid1()) + ".pcap"
#                 output_path = "output.pcap"
#                 start_sniffing_cmd = ["tshark",
#                                       "-i", interface_filter,
#                                       "-w", output_path, # Path to the stored PCAP
#                                       "-f", sniffer_filter, # sniffing filter
#                 ]
#                 p = subprocess.Popen(start_sniffing_cmd)
#                 self.sniffer_process.add(p)
#             elif msg["order"] == "finishSniffer":
#                 log.info("Stop the sniffer")
#                 for p in self.sniffer_process:
#                     p.terminate()
#             elif msg["order"] == "getPcap":
#                 log.info("PCAP collection")
#                 with open("output.pcap", "rb") as f:
#                     ans = json.dumps({
#                             "msg_id": str(uuid.uuid1()),
#                             "src": "amqp://user_id@finterop.org/agent/agent_id",
#                             "timestamp": "42",
#                             "topic": "pkt.network",
#                             "props": {
#                                 "pkt": base64.b64encode(f.read()).decode()}
#                         }
#                     )
#                     log.debug(ans)
#                     self.producer.publish(ans,
#                         exchange=self.exchange,
#                         routing_key="pkt.network")
#             else:
#                 log.error("Unknown command")
#         else:
#             log.info("No order in the message")


#         self.tun._v6ToInternet_notif(sender="test",
#                                      signal="tun",
#                                      data=msg["data"])


class TunConnector(BaseController):
    """

    """

    NAME = "tun"

    def __init__(self, **kwargs):
        """

        Args:
            key: ZMQ message
        """
        super(TunConnector, self).__init__(name=TunConnector.NAME)
        self.tun = None
        kwargs["consumer_name"] = TunConnector.NAME
        self.consumer = TunConsumer(**kwargs)
        self.consumer.log = logging.getLogger(__name__)
        self.consumer.log.setLevel(logging.DEBUG)

    def run(self):
        self.consumer.run()
