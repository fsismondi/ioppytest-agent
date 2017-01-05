"""
Plugin to connect to the F-interop backend
"""
import json
import logging

from .base import BaseController, BaseConsumer


__version__ = (0, 0, 1)


log = logging.getLogger(__name__)


class CoreConsumer(BaseConsumer):
    """
    AMQP helper
    """

    def __init__(self, user, password, session, server, name, consumer_name):
        super(CoreConsumer, self).__init__(user, password, session, server, name, consumer_name)

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
        log.info("Backend ready to consume data")
        log.info("-------------------------------------------------")
        log.info("Go to this URL: http://{platform}/session/{session}".format(platform=self.server_url,
                                                                              session=self.session))
        log.info("-------------------------------------------------")

    def handle_control(self, body, message):
        log.debug("DEFAULT HANDLE CONTROL")
        log.debug(("Payload", message.payload))
        log.debug(("Properties", message.properties))
        log.debug(("Headers", message.headers))
        log.debug(("body", message.body))
        msg = None
        try:
            msg = json.loads(body)
            log.debug(message)
        except ValueError as e:
            message.ack()
            log.error(e)
            log.error("Incorrect message: {0}".format(body))

        if msg is not None:
            log.debug("Just received that packet")
            log.debug(msg)


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
