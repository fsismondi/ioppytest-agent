"""

"""
import json
import logging
from multiprocessing import Process

from ..utils.messages import Message as EventBusMessage

from amqp.exceptions import UnexpectedFrame
from kombu import Connection, Queue, Exchange, Consumer
from kombu.mixins import ConsumerMixin


class BaseConsumer(ConsumerMixin):
    DEFAULT_EXCHANGE_NAME = "amq.topic"
    AMQP_CONNECTION_TIMEOUT = 10

    def __init__(self, user, password, session, server, exchange, name, consumer_name, topics):
        """

        Args:
            user: Username
            password: User password
            session: Test session
            server: Backend for the RMQ
            exchange: RMQ exchange for sending messages
            name: Identity of the agent. Used by testing tools to identify/differentiate each agent on the session
            consumer_name: Name to easily identify a process consuming.
            topics: Topics subscriptions for the consumer
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
                                     transport_options={'confirm_publish': True},
                                     connect_timeout=self.AMQP_CONNECTION_TIMEOUT)

        if exchange:
            self.exchange = Exchange(exchange,
                                     type="topic",
                                     durable=True)
        else:
            self.exchange = Exchange(BaseConsumer.DEFAULT_EXCHANGE_NAME,
                                     type="topic",
                                     durable=True)

        # queues created for topic subscriptions
        self.queues = []

        # handle subscriptions
        self.subscribe_to_topics(topics)

    def subscribe_to_topics(self, topic_list):
        for t in topic_list:
            queue = Queue(
                name="consumer: {name}.{consumer_name}?rkey={rkey}".format(
                    name=self.name,
                    consumer_name=self.consumer_name,
                    rkey=t
                ),
                exchange=self.exchange,
                routing_key=t,
                durable=False,
                auto_delete=True
            )

            self.queues.append(
                queue
            )

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(self.queues, callbacks=[self.on_message], accept=['json']),
        ]

    def on_message(self, body, message):
        assert type(body) is dict  # assert that kombu deserialized it already
        json_body = json.dumps(body)

        self.log.debug("base on_message() callback, got: {}".format(message.delivery_info.get('routing_key')))
        msg = EventBusMessage.load(json_body, message.delivery_info.get('routing_key'))
        try:
            self._on_message(msg)
        except UnexpectedFrame as uf_err:
            self.log.error(
                uf_err.message
            )

    def _on_message(self, message):
        "Class to be overridden by children class"
        raise NotImplementedError()

    def on_consume_ready(self, connection, channel, consumers, wakeup=True, **kwargs):
        # control plane info
        for q in self.queues:
            self.log.info("Queue: {queue_name} bound to: {rkey} ".format(queue_name=q.name, rkey=q.routing_key))


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
