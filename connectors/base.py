"""

"""
import json
import logging
from multiprocessing import Process

from kombu import Connection
from kombu import Exchange
from kombu import Queue
from kombu.mixins import ConsumerMixin


DEFAULT_EXCHANGE_NAME = "default"


class BaseConsumer(ConsumerMixin):
    DEFAULT_EXCHANGE_NAME = "default"

    def __init__(self, user, password, session, server, name, consumer_name):
        """

        Args:
            user: Username
            password: User password
            session: Test session
            server: Backend for the RMQ
            name: Identity of the component. Can be an UUID or a human nickname
            consumer_name: Name to easily identify a process consuming.
        """
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.DEBUG)

        self.user = user
        self.password = password
        self.session = session
        self.server = server
        self.name = name
        self.consumer_name = consumer_name
        self.server_url = 'amqp://{user}:{password}@{server}/{session}'.format(user=user,
                                                                               password=password,
                                                                               session=session,
                                                                               server=server)
        self.connection = Connection(self.server_url,
                                     transport_options={'confirm_publish': True})

        self.exchange = Exchange(BaseConsumer.DEFAULT_EXCHANGE_NAME,
                                 type="topic",
                                 durable=True)

        self.control_queue = Queue("control.{consumer_name}@{name}".format(name=name,
                                                                           consumer_name=consumer_name),
                                   exchange=self.exchange,
                                   routing_key='control.{consumer_name}.#.{name}'.format(consumer_name=consumer_name,
                                                                                         name=name),
                                   durable=False)

        self.data_queue = Queue("data.{consumer_name}@{name}".format(name=name,
                                                                     consumer_name=consumer_name),
                                exchange=self.exchange,
                                routing_key='data.{consumer_name}.#.{name}'.format(consumer_name=consumer_name,
                                                                                   name=name),
                                durable=False)

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(queues=[self.control_queue],
                     callbacks=[self.handle_control],
                     no_ack=True,
                     accept=['json']),
            Consumer(queues=[self.data_queue],
                     callbacks=[self.handle_data],
                     no_ack=True,
                     accept=["json"])
        ]

    def on_consume_ready(self, connection, channel, consumers, wakeup=True, **kwargs):
        self.log.info("{consumer_name} ready to consume data. Typical routing key: control.{consumer_name}@{name}".format(consumer_name=self.consumer_name, name=self.name))

    def handle_control(self, body, message):
        self.log.debug("DEFAULT HANDLE CONTROL")
        self.log.debug(("Payload", message.payload))
        self.log.debug(("Properties", message.properties))
        self.log.debug(("Headers", message.headers))
        self.log.debug(("body", message.body))
        msg = None
        try:
            msg = json.loads(body)
            self.log.debug(message)
        except ValueError as e:
            message.ack()
            self.log.error(e)
            self.log.error("Incorrect message: {0}".format(body))

        if msg is not None:
            self.log.debug("Just received that packet")
            self.log.debug(msg)

    def handle_data(self, body, message):
        """

        Args:
            msg:

        Returns:

        """
        self.log.debug("DEFAULT HANDLE DATA")
        self.log.debug(("Payload", message.payload))
        self.log.debug(("Properties", message.properties))
        self.log.debug(("Headers", message.headers))
        self.log.debug(("body", message.body))
        # msg = None
        # try:
        #     msg = json.loads(body)
        #     self.log.debug(message)
        # except ValueError as e:
        #     message.ack()
        #     self.log.error(e)
        #     self.log.error("Incorrect message: {0}".format(body))
        #
        # if msg is not None:
        #     self.log.debug("Just received that packet")
        #     self.log.debug(msg)

    def test_connection(self):
        """
        Test if a component can talk on the event bus.

        Returns:

        """
        #     for key in [control key, data key]:
        #         log.info("Testing on local routing key: %s" % key)
        #         self.basic_publish(key, "PING!!")
        pass


class BaseController(Process):
    """

    """

    def __init__(self, name, process_args=None):
        if process_args is not None:
            super(BaseController, self).__init__(**process_args)
        else:
            super(BaseController, self).__init__()
        self.go_on = True
        self.name = name
