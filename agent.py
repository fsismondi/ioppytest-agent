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

from connectors.tun import TunConnector
from connectors.core import CoreConnector
from connectors.http import HTTPConnector
from connectors.ping import PingConnector
from connectors.zeromq import ZMQConnector
from connectors.serialconn import SerialConnector

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

__version__ = (0, 0, 1)

DEFAULT_PLATFORM = 'f-interop.paris.inria.fr'
LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
logging.getLogger('amqp').setLevel(logging.INFO)

class Agent(object):
    """
    Command line interface of the agent
    """

    header = """
F-interop agent and management tool.

Please use the following format to connect to the f-interop server:

sudo python -m agent connect --url amqp://f_interop_user:f_interop_password@f_interop_server/session_id --name agent_name

For more information, visit: http://f-interop.paris.inria.fr.
""",

    def __init__(self):

        self.cli = click.Group(
            add_help_option=Agent.header,
            short_help=Agent.header
        )

        self.session_url = click.Option(
            param_decls=["--url"],
            default= "amqp://guest:guest@localhost/default",
            required=True,
            help="")

        self.name_option = click.Option(
            param_decls=["--name"],
            default=str(uuid.uuid1()),
            required=False,
            help="Agent identity (default: random generated)")

        # Commands

        self.connect_command = click.Command(
            "connect",
            callback=self.handle_connect,
            params=[
                self.session_url,
                self.name_option,
                    ],
            short_help="Authenticate user"
        )

        self.cli.add_command(self.connect_command)

        self.plugins = {}

    def handle_connect(self, url, name):
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
        log.info("Try to connect with %s" % data)

        self.plugins["core"] = CoreConnector(**data)
        self.plugins["tun"] = TunConnector(**data)
        self.plugins["zmq"] = ZMQConnector(**data)
        self.plugins["ping"] = PingConnector(**data)
        self.plugins["http"] = HTTPConnector(**data)
        self.plugins["serial"] = SerialConnector(**data)

        for p in self.plugins.values():
            p.start()

    def run(self):
        self.cli()

if __name__ == "__main__":

    agent = Agent()
    agent.run()

    # try:
    #     # Loop designed to catch the keyboard interruption
    #
    #     while any(map(lambda x: x.is_alive(), agent.plugins)):
    #         # print([x.isAlive() for x in plugins])
    #         pass
    #
    # except KeyboardInterrupt as SystemExit:
    #     for plugin in agent.plugins:
    #         plugin.go_on = False
    #     time.sleep(1)
    #     log.critical('! Received keyboard interrupt, quitting threads.\n')
