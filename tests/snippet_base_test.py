class MyTest(ConsumerMixin):

    def __init__(self, connection, name="myTest"):
        self.name = name
        self.connection = connection
        self.producer = self.connection.Producer(serializer='json')

        self.exchange = Exchange('default', type="topic", durable=True)
        self.control_queue = Queue("control_{name}".format(name=name),
                                   exchange=self.exchange,
                                   durable=True,
                                   routing_key="control.fromAgent.#")
        self.data_queue = Queue("data_{name}".format(name=name),
                                exchange=self.exchange,
                                durable=True,
                                routing_key="data.fromAgent.#")
        self.tun = OpenTunLinux(
            name=self.name,
            rmq_connection=self.connection,
            ipv6_host=":2",
            ipv6_prefix=DEFAULT_IPV6_PREFIX
        )

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