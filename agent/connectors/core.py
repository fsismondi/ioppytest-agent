"""
Plugin to connect to the AMQP broker
"""
import json
import logging
from kombu import Producer

from .base import BaseController, BaseConsumer
from ..utils.messages import MsgTestingToolComponentReady

__version__ = (0, 1, 0)

log = logging.getLogger(__name__)


class CoreConsumer(BaseConsumer):
    """
    AMQP helper
    """

    def __init__(self, user, password, session, server, exchange, name, consumer_name):
        subscriptions = [MsgTestingToolComponentReady.routing_key]
        super(CoreConsumer, self).__init__(user, password, session, server, exchange, name, consumer_name,
                                           subscriptions)

    def on_consume_ready(self, connection, channel, consumers, wakeup=True, **kwargs):

        #  let's send bootstrap message
        msg = MsgTestingToolComponentReady(
            component=self.name,
            description="Component READY to start test suite."
        )

        producer = Producer(connection, serializer='json')
        producer.publish(
            body=msg.to_dict(),
            exchange=self.exchange,
            routing_key=msg.routing_key
        )

        log.info("Agent READY, listening on the event bus for ctrl messages and data packets...")

    def _on_message(self, message):
        self.log.warning(
            "<{consumer_name}> got {message}, no callback bound to it.".format(
                consumer_name=self.consumer_name,
                message=repr(message)
            )
        )


class CoreConnector(BaseController):
    """

    """

    NAME = "core"

    def __init__(self, **kwargs):
        """

        Args:
            key:
        """

        super(CoreConnector, self).__init__(name=CoreConnector.NAME)

        kwargs["consumer_name"] = CoreConnector.NAME
        self.consumer = CoreConsumer(**kwargs)

    def run(self):
        """

        Returns:

        """
        self.consumer.run()
