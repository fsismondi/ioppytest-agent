# coding: utf-8


"""
ioppytest-agent CLI:
********************

Installation
------------

TBD

Features of the agent
----------------------

* The agent must be able to inject packets in the local loop or re-emit packets it receives
  from the testing tool.

* The agent MUST be able to authenticate itself with the backend.

* The agent will monitor all the network traffic passing through it and send it to the backend.

* The agent isn't the way the user interact with test coordinator/manager. It simply connects to backend to establish a
 sort of virtual network.
"""
from __future__ import absolute_import

import os
import logging
import click

from .connectors import TunConnector
from .connectors import CoreConnector

from .utils import ioppytest_banner
from .utils import packet_dumper

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

DEFAULT_PLATFORM = 'f-interop.rennes.inria.fr'
LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
logging.getLogger('amqp').setLevel(logging.INFO)

default_ip_configs = {
    'agent_1': ('bbbb', '1', '10.2.0.1'),
    'agent_2': ('bbbb', '2', '10.2.0.2'),
    'agent_3': ('bbbb', '3', '10.2.0.3'),
    'agent_4': ('bbbb', '4', '10.2.0.4'),
    'agent_5': ('bbbb', '5', '10.2.0.5'),
    'agent_6': ('bbbb', '6', '10.2.0.6'),
}


class Agent(object):
    """
    Command line interface of the agent
    """

    header = """ 
    
---------------------------------------------------------------------

For discovering all agent features and please see:

- general info: README.md

- installing the agent: INSTALL.md

- using the agent: USAGE.md

- frequently asked questions: FAQ.md

- license: LICENSE

at https://github.com/fsismondi/ioppytest-agent

---------------------------------------------------------------------

"""

    default_AMQP_URL = 'amqp://guest:guest@localhost/'

    def __init__(self):

        print(ioppytest_banner)

        self.cli = click.Group(
            add_help_option=Agent.header,
            help=Agent.header
        )

        self.session_url = click.Option(
            param_decls=["--url"],
            default=None,
            required=False,
            help='url of the session, if None then uses AMQP_ENV env var or else {}'.format(self.default_AMQP_URL))

        self.session_amqp_exchange = click.Option(
            param_decls=["--exchange"],
            default="amq.topic",
            required=False,
            help="AMQP exchange used in the session")

        self.name_option = click.Option(
            param_decls=["--name"],
            required=True,
            help="Agent identity, normally associated with the IUT role (coap_client, comi_server, etc)")

        self.dump_option = click.Option(
            param_decls=["--dump"],
            default=False,
            required=False,
            help="[WIP] Dump automatically data packets from event bus into pcap files",
            is_flag=True)

        self.force_bootstrap = click.Option(
            param_decls=["--force-bootstrap"],
            default=True,
            required=False,
            help="Force agent's bootstrap",
            is_flag=True)

        self.ipv6_prefix = click.Option(
            param_decls=["--ipv6-prefix"],
            default=None,
            required=False,
            help="Prefix of IPv6 address, used only if --force-bootstrap")

        self.ipv6_host = click.Option(
            param_decls=["--ipv6-host"],
            default=None,
            required=False,
            help="Host IPv6 address, used only if --force-bootstrap")

        self.ipv4_address = click.Option(
            param_decls=["--ipv4-address"],
            required=False,
            help="IPv4 address, used only if --force-bootstrap")

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
                self.ipv4_address,
            ],
            short_help="Connect with authentication AMQP_URL, and some other basic agent configurations"
        )

        self.cli.add_command(self.connect_command)

        self.plugins = {}

    def handle_connect(self, url, exchange, name, dump, force_bootstrap, ipv6_host, ipv6_prefix, ipv4_address):
        """
        Authenticate USER and create agent connection to AMQP broker.

        """

        # - - - Manage default config
        if url is None:
            url = os.getenv('AMQP_URL')
        if url is None:
            url = self.default_AMQP_URL

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

        # all 3 ip params must be set, else we use default_ip_configs
        if not (ipv6_prefix and ipv6_host and ipv4_address):
            ipv6_prefix, ipv6_host, ipv4_address = default_ip_configs[name]

        # - - - Setup plugins
        log.info("Try to connect with %s" % data)

        self.plugins["core"] = CoreConnector(**data)

        data['force_bootstrap'] = force_bootstrap
        data['ipv6_host'] = ipv6_host
        data['ipv6_prefix'] = ipv6_prefix
        data['ipv4_address'] = ipv4_address
        self.plugins["tun"] = TunConnector(**data)

        # - - - Manage threads

        for p in self.plugins.values():
            p.start()

            # TODO re-implement with kombu and BaseController/CoreConsumer
            # TODO fix pcap_dumper support for py2, python3 -m utils.packet_dumper works fine tho

            # if dump:
            #     dump_p = multiprocessing.Process(target=packet_dumper.launch_amqp_data_to_pcap_dumper, args=())
            #     dump_p.start()

    def run(self):
        self.cli()


def main():
    agent = Agent()
    agent.run()


if __name__ == "__main__":
    main()
