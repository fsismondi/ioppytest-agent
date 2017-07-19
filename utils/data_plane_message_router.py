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
COMPONENT_ID = 'packet_router_snippet'

AGENT_1_ID = 'coap_client_agent'
AGENT_2_ID = 'coap_server_agent'
AGENT_TT_ID = 'agent_TT'
# init logging to stnd output and log files
logger = logging.getLogger(__name__)

# default handler
sh = logging.StreamHandler()
logger.addHandler(sh)

logger.setLevel(logging.DEBUG)


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
    AGENT_2_ID = 'coap_server_agent'
    AGENT_TT_ID = 'agent_TT'
    DEFAULT_ROUTING = {'data.tun.fromAgent.%s' % AGENT_1_ID: ['data.tun.toAgent.%s' % AGENT_2_ID,
                                                              'data.tun.toAgent.%s' % AGENT_TT_ID
                                                              ],
                       'data.tun.fromAgent.%s' % AGENT_2_ID: ['data.tun.toAgent.%s' % AGENT_1_ID,
                                                              'data.tun.toAgent.%s' % AGENT_TT_ID
                                                              ],
                       }

    def __init__(self, conn, routing_table=None):
        threading.Thread.__init__(self)

        if routing_table:
            self.routing_table = routing_table
        else:
            self.routing_table = PacketRouter.DEFAULT_ROUTING

        logger.info('routing table (rkey_src:[rkey_dst]) : {table}'.format(table=json.dumps(self.routing_table)))

        # queues & default exchange declaration
        self.message_count = 0
        self.connection = conn
        self.channel = self.connection.channel()
        self.queues_init()

        logger.info('packet router waiting for new messages in the data plane..')

    def queues_init(self):
        for src_rkey, dst_rkey_list in self.routing_table.items():
            assert type(src_rkey) is str
            assert type(dst_rkey_list) is list

            src_queue = '%s@%s' % (src_rkey, COMPONENT_ID)

            self.channel.queue_declare(queue=src_queue, auto_delete=False)
            self.channel.queue_bind(exchange=AMQP_EXCHANGE,
                                    queue=src_queue,
                                    routing_key=src_rkey)

            # bind all src queues to on_request callback
            self.channel.basic_consume(self.on_request, queue=src_queue)

            for dst_rkey in dst_rkey_list:
                # start with clean queues
                dst_queue = '%s@%s_raw_packet_logs' % (dst_rkey, COMPONENT_ID)
                self.channel.queue_delete(dst_queue)
                self.channel.queue_declare(queue=dst_queue, auto_delete=False, arguments={'x-max-length': 10})
                self.channel.queue_bind(exchange=AMQP_EXCHANGE,
                                        queue=src_queue,
                                        routing_key=dst_rkey)

    def stop(self):
        self.channel.stop_consuming()

    def on_request(self, ch, method, props, body):

        # TODO implement forced message drop mechanism

        # obj hook so json.loads respects the order of the fields sent -just for visualization purposeses-
        body_dict = json.loads(body.decode('utf-8'), object_pairs_hook=OrderedDict)
        ch.basic_ack(delivery_tag=method.delivery_tag)

        try:
            logger.debug("Message sniffed: %s" % (body_dict['_type']))
        except KeyError:
            logger.warning("Incorrect formatted message received in event bus")

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
            data_slip = body_dict['data_slip']
        except:
            logger.error('wrong message format, no data field found in : {msg}'.format(msg=json.dumps(body_dict)))
            return

        src_rkey = method.routing_key
        if src_rkey in self.routing_table.keys():
            list_dst_rkey = self.routing_table[src_rkey]
            for dst_rkey in list_dst_rkey:
                # resend to dst_rkey
                self.channel.basic_publish(
                    body=json.dumps({'_type': 'packet.sniffed.raw', 'data': data, 'data_slip': data_slip}),
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

        sys.exit(1)


    signal.signal(signal.SIGINT, signal_int_handler)

    # routing tables for between agents' TUNs interfaces and also between agents' serial interfaces
    iut_routing_table_serial = {
        'data.serial.fromAgent.%s' % AGENT_1_ID: ['data.serial.toAgent.%s' % AGENT_2_ID,
                                                  ],
        'data.serial.fromAgent.%s' % AGENT_2_ID: ['data.serial.toAgent.%s' % AGENT_1_ID,
                                                  ],
    }

    iut_routing_table_tun = {
        'data.tun.fromAgent.%s' % AGENT_1_ID: ['data.tun.toAgent.%s' % AGENT_2_ID,
                                               'data.tun.toAgent.%s' % AGENT_TT_ID
                                               ],
        'data.tun.fromAgent.%s' % AGENT_2_ID: ['data.tun.toAgent.%s' % AGENT_1_ID,
                                               'data.tun.toAgent.%s' % AGENT_TT_ID
                                               ],
    }

    routing_table = dict()
    routing_table.update(iut_routing_table_serial)
    routing_table.update(iut_routing_table_tun)

    # in case its not declared
    connection.channel().exchange_declare(exchange=AMQP_EXCHANGE,
                                          type='topic',
                                          durable=True,
                                          )

    # start amqp router thread
    r = PacketRouter(connection, routing_table)
    r.start()
