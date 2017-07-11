# -*- coding: utf-8 -*-
# !/usr/bin/env python3
import pika
import threading
import json
from collections import OrderedDict
import datetime
import signal
import sys
import os
import logging

AMQP_URL = str(os.environ['AMQP_URL'])
AMQP_EXCHANGE = str(os.environ['AMQP_EXCHANGE'])

COMPONENT_ID = 'packet_router'
# init logging to stnd output and log files
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# default handler
sh = logging.StreamHandler()
logger.addHandler(sh)



def publish_message(channel, message):
    """ Published which uses message object metadata

    :param channel:
    :param message:
    :return:
    """

    properties = pika.BasicProperties(**message.get_properties())

    channel.basic_publish(
            exchange=AMQP_EXCHANGE,
            routing_key=message.routing_key,
            properties=properties,
            body=message.to_json(),
    )


class PacketRouter(threading.Thread):
    AGENT_1_ID = 'coap_client_agent'
    AGENT_2_ID = 'coap_client_agent'
    AGENT_TT_ID = 'agent_TT'

    def __init__(self, conn, routing_table=None):
        threading.Thread.__init__(self)


        if routing_table:
            self.routing_table = routing_table
        else:
            # default routing
            # agent_TT is the agent instantiated by the testing tool
            self.routing_table = {
                # first two entries is for a user to user setup
                'data.serial.fromAgent.%s' % PacketRouter.AGENT_1_ID:
                    [
                        'data.serial.toAgent.%s' % PacketRouter.AGENT_2_ID,
                        'data.serial.toAgent.%s' % PacketRouter.AGENT_TT_ID
                    ],
                'data.serial.fromAgent.%s' % PacketRouter.AGENT_2_ID:
                    [
                        'data.serial.toAgent.%s' % PacketRouter.AGENT_1_ID,
                        'data.serial.toAgent.%s' % PacketRouter.AGENT_TT_ID
                    ],
            }

        logger.info('routing table (rkey_src:[rkey_dst]) : {table}'.format(table=json.dumps(self.routing_table)))

        # queues & default exchange declaration
        self.message_count = 0

        self.connection = conn

        self.channel = self.connection.channel()

        queue_name = 'data_packets_queue@%s' % COMPONENT_ID
        self.channel.queue_declare(queue=queue_name, auto_delete=True)

        self.channel.queue_bind(exchange=AMQP_EXCHANGE,
                                queue=queue_name,
                                routing_key='data.tun.fromAgent.#')


        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.on_request, queue=queue_name)

    def stop(self):
        self.channel.stop_consuming()

    def on_request(self, ch, method, props, body):
        # obj hook so json.loads respects the order of the fields sent -just for visualization purposeses-
        body_dict = json.loads(body.decode('utf-8'), object_pairs_hook=OrderedDict)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.debug("Message sniffed: %s" % (body_dict['_type']))
        self.message_count += 1

        print('\n* * * * * * MESSAGE SNIFFED (%s) * * * * * * *' % self.message_count)
        print("TIME: %s" % datetime.datetime.time(datetime.datetime.now()))
        print(" - - - ")
        print("ROUTING_KEY: %s" % method.routing_key)
        print(" - - - ")
        print("HEADERS: %s" % props.headers)
        print(" - - - ")
        print("PROPS: %s" % json.dumps(
                {
                    'content_type': props.content_type,
                    'content_encoding': props.content_encoding,
                    'headers': props.headers,
                    'delivery_mode': props.delivery_mode,
                    'priority': props.priority,
                    'correlation_id': props.correlation_id,
                    'reply_to': props.reply_to,
                    'expiration': props.expiration,
                    'message_id': props.message_id,
                    'timestamp': props.timestamp,
                    'user_id': props.user_id,
                    'app_id': props.app_id,
                    'cluster_id': props.cluster_id,
                }
        )
              )
        print(" - - - ")
        print('BODY %s' % json.dumps(body_dict))
        print(" - - - ")
        # print("ERRORS: %s" % )
        print('* * * * * * * * * * * * * * * * * * * * * \n')

        # let's route the message to the right agent

        try:
            data = body_dict['data']
        except:
            logger.error('wrong message format, no data field found in : {msg}'.format(msg=json.dumps(body_dict)))
            return

        src_rkey = method.routing_key
        if src_rkey in self.routing_table.keys():
            list_dst_rkey = self.routing_table[src_rkey]
            for dst_rkey in list_dst_rkey:
                # resend to dst_rkey
                self.channel.basic_publish(
                        body=json.dumps({'_type': 'packet.to_inject.raw', 'data': data}),
                        routing_key=dst_rkey,
                        exchange=AMQP_EXCHANGE,
                        properties=pika.BasicProperties(
                                content_type='application/json',
                        )
                )

                logger.info(
                    "Routing packet (%d) from topic: %s to topic: %s" % (self.message_count, src_rkey, dst_rkey))

        else:
            logger.warning('No known route for r_key source: {r_key}'.format(r_key=src_rkey))
            return

    def run(self):
        self.channel.start_consuming()
        logger.info('Bye byes!')


###############################################################################

if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.URLParameters(AMQP_URL))
    channel = connection.channel()


    def signal_int_handler(channel):
        # FINISHING... let's send a goodby message
        msg = {
            'message': '{component} is out! Bye bye..'.format(component=COMPONENT_ID),
            "_type": '{component}.shutdown'.format(component=COMPONENT_ID)
        }
        channel.basic_publish(
                body=json.dumps(msg),
                routing_key='control.session.info',
                exchange=AMQP_EXCHANGE,
                properties=pika.BasicProperties(
                        content_type='application/json',
                )
        )

        logger.info('got SIGINT. Bye bye!')

        sys.exit(0)


    signal.signal(signal.SIGINT, signal_int_handler)

    # in case its not declared
    connection.channel().exchange_declare(exchange=AMQP_EXCHANGE,
                                          type='topic',
                                          durable=True,
                                          )

    # start amqp router thread
    r = PacketRouter(connection, None)
    r.start()
