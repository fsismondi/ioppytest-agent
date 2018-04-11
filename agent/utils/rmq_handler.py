import logging
import pika
import time

class RabbitMQHandler(logging.Handler):
    """
     A handler that acts as a RabbitMQ publisher
     Requires the kombu module.
     Example setup::
        handler = RabbitMQHandler('amqp://guest:guest@localhost')
    """
    def __init__(self, url, name, exchange="amq.topic"):
        logging.Handler.__init__(self)
        self.connection = pika.BlockingConnection(pika.URLParameters(url))
        self.channel = self.connection.channel()
        self.exchange = exchange
        self.name = name

    def emit(self, record):
        routing_key = ".".join(["log", record.levelname.lower(), self.name])
        self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=record.msg)

    def close(self):
        self.channel.close()

if __name__ == "__main__":
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    rabbitmq_handler = RabbitMQHandler('amqp://guest:guest@localhost', "MyComponent")
    log.addHandler(rabbitmq_handler)
    sh = logging.StreamHandler()
    log.addHandler(sh)
    while True:
        log.critical("This is a critical message")
        time.sleep(1)
        log.error("This is an error")
        time.sleep(1)
        log.warning("This is a warning")
        time.sleep(1)
        log.info("This is an info")
        time.sleep(1)
        log.debug("This is a debug")