# coding: utf-8


"""
Agent for f-interop
*******************

Installation
------------

The installation for the user is supposed to be as simple as possible. Ideally, the user
should only have the ./finterop tool installed with the relevant dependencies and should
be ready to go.

Features of the agent
----------------------

* The agent must be able to inject packets in the local loop or re-emit packets it receives
  from the f-interop backend.

* The agent MUST be able to authenticate itself with the backend.

* The agent will monitor all the network traffic passing through it and send it to the backend.

* The agent isn't the way the user interact with test. It simply connects to f-interop and from there receive
instruction. All the commands send from the agent are for debugging and developing purposes and won't be enabled
by default in the final version.
"""
import logging
import click
import uuid
import multiprocessing

from connectors.tun import TunConnector
from connectors.core import CoreConnector
from connectors.http import HTTPConnector
from connectors.serialconn import SerialConnector

from utils import arrow_down, arrow_up, finterop_banner
from utils.packet_dumper import launch_amqp_data_to_pcap_dumper

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

__version__ = (0, 1, 0)

DEFAULT_PLATFORM = 'f-interop.paris.inria.fr'
LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
logging.getLogger('amqp').setLevel(logging.INFO)


class Agent(object):
    """
    Command line interface of the agent
    """

    header = """
Agent (~VPN client) for connecting your implementation under test (IUT) to the private network of the remote interop 
session.

Some examples on the different modes of running the agent (depending on the cabling and networking of your IUT):

---------------------------------------------------------------------
Note: We assume that a session was a already created and user has url
and it has been exported as environment variable

e.g.:
export AMQP_URL=amqp://alfredo:zitarrosa@exampleRmqHost[:port]/sessionXX 
---------------------------------------------------------------------

1. user runs an IPv6 based implementation (e.g. coap_client) which runs in same PC where agent runs (default mode):


\b
command:
    sudo python -m agent connect \  
        --url $AMQP_URL \ 
        --name coap_client

expected result:

agent is connected to f-interop and now awaits bootstrap command from backend

---------------------------------------------------------------------

2. user runs an IPv6 based implementation (e.g. coap_client) which runs in same PC where agent runs, but wants to force 
bootstrap ( virtual interface creation, and forced IP assignation)

\b
command:
    sudo python -m agent connect  \ 
        --url $AMQP_URL \ 
        --name coap_client \ 
        --force-bootstrap \ 
        --ipv6-prefix bbbb \ 
        --ipv6-host 100
    
expected result:
    agent is connected to f-interop, bootstrapped, and has an assigned 
    IPv6 (check interface with ifconfig)

---------------------------------------------------------------------
continue writing this...

TODO document --serial for 802.15.4 probes

TODO document --router-mode for re-routing the packets to another interface

\b
---------------------------------------------------------------------
For exploring all "connect" command option type: python -m agent connect  --help
For more information visit: http://doc.f-interop.eu
---------------------------------------------------------------------

"""

    def __init__(self):

        print(finterop_banner)

        self.cli = click.Group(
            add_help_option=Agent.header,
            help=Agent.header
        )

        self.session_url = click.Option(
            param_decls=["--url"],
            default="amqp://guest:guest@localhost/",
            required=True,
            help="AMQP url provided by F-Interop")

        self.session_amqp_exchange = click.Option(
            param_decls=["--exchange"],
            default="amq.topic",
            required=False,
            help="AMQP exchange used in the session")

        self.name_option = click.Option(
            param_decls=["--name"],
            default=str(uuid.uuid1()),
            required=False,
            help="Agent identity (default: random generated)")

        self.dump_option = click.Option(
            param_decls=["--dump"],
            default=False,
            required=False,
            help="[NOT YET SUPPORTED] Dump automatically data packets from event bus into pcap files",
            is_flag=True)

        self.force_bootstrap = click.Option(
            param_decls=["--force-bootstrap"],
            default=False,
            required=False,
            help="Force agent's bootstrap",
            is_flag=True)

        self.ipv6_prefix = click.Option(
            param_decls=["--ipv6-prefix"],
            default="bbbb",
            required=False,
            help="Prefix of IPv6 address, used only if --force-bootstrap")

        self.ipv6_host = click.Option(
            param_decls=["--ipv6-host"],
            default="1",
            required=False,
            help="Host IPv6 address, used only if --force-bootstrap")

        self.serial_option = click.Option(
            param_decls=["--serial"],
            default=False,
            required=False,
            help="Run agent bound to serial injector/forwarder of 802.15.4 frames",
            is_flag=True)

        # Commands

        self.connect_command = click.Command(
            "connect",
            callback=self.handle_connect,
            params=[
                self.session_url,
                self.session_amqp_exchange,
                self.name_option,
                self.dump_option,
                self.force_bootstrap,
                self.ipv6_host,
                self.ipv6_prefix,
                self.serial_option,
            ],
            short_help="Connect with authentication AMQP_URL, and some other basic agent configurations"
        )

        self.cli.add_command(self.connect_command)

        self.plugins = {}

    def handle_connect(self, url, exchange, name, dump, force_bootstrap, ipv6_host, ipv6_prefix, serial):
        """
        Authenticate USER and create agent connection to f-interop.

        """

        p = urlparse(url)
        data = {
            "user": p.username,
            "password": p.password,
            "session": p.path.strip('/'),
            "server": p.hostname,
            "name": name,
        }

        if exchange:
            data.update({'exchange': exchange})

        if p.port:
            data.update({"server": "{}:{}".format(p.hostname, p.port)})

        log.info("Try to connect with %s" % data)

        self.plugins["core"] = CoreConnector(**data)

        if serial:
            self.plugins["serial"] = SerialConnector(**data)

        else:
            # pass some extra kwargs specific to the TunConnector
            data['force_bootstrap'] = force_bootstrap
            data['ipv6_host'] = ipv6_host
            data['ipv6_prefix'] = ipv6_prefix
            self.plugins["tun"] = TunConnector(**data)

        for p in self.plugins.values():
            p.start()

            # TODO re-implement with kombu and BaseController/CoreConsumer
            # TODO fix pcap_dumper support for py2, python3 -m utils.packet_dumper works fine tho

            # if dump:
            #     dump_p = multiprocessing.Process(target=launch_amqp_data_to_pcap_dumper, args=())
            #     dump_p.start()

    def run(self):
        self.cli()


if __name__ == "__main__":
    agent = Agent()
    agent.run()
