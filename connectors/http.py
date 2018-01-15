import json

__version__ = (0, 1, 0)

import logging
from requests import Request, Session


from .base import BaseController, BaseConsumer

log = logging.getLogger(__name__)


class HTTPConsumer(BaseConsumer):
    """
    AMQP helper
    """

    def __init__(self, user, password, session, server, exchange, name, consumer_name):
        super(HTTPConsumer, self).__init__(user, password, session, server, exchange, name, consumer_name)

    def handle_control(self, body, message):
        """

        Args:
            body:
            message:

        Returns:

        """
        required_keys = {"url", "verb", "data"}
        msg = None
        try:
            msg = json.loads(body)
            self.log.debug(message)
        except ValueError as e:
            message.ack()
            self.log.error(e)
            self.log.error("Incorrect message: {0}".format(body))

        if msg is not None:
            present_keys = set(msg.keys())
            if not present_keys.issuperset(required_keys):
                self.log.error("Error you need those keys: %s" % required_keys)
            else:
                s = Session()
                req = Request(msg["verb"], msg["url"], data=msg["data"])

                prepped = s.prepare_request(req)

                resp = s.send(prepped)

                self.log.info(resp.status_code)


class HTTPConnector(BaseController):
    NAME = "http"

    def __init__(self, **kwargs):
        super(HTTPConnector, self).__init__(name=HTTPConnector.NAME)
        kwargs["consumer_name"] = HTTPConnector.NAME
        self.consumer = HTTPConsumer(**kwargs)
        self.consumer.log = logging.getLogger(__name__)
        self.consumer.log.setLevel(logging.DEBUG)

    def run(self):
        self.consumer.run()
