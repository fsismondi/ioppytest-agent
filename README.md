Agent for the f-interop platform (ioppytest-agent)
--------------------------------------------------

Design
------
The design of the f-interop agent is modular by design.
An agent is made of different processes that connect to AMQP message
broker and exchange messages (in and out) with other components using
the same AMQP broker.

Note well
----
Agent is only supported by python2 -> tun librarires py2 only

Core
----
When started, the agent starts up the core module. This component is in
charge of launching all the other components.
If new components needs to be added they just need to be launched
from this component.

Core open the default ZMQ socket that is used by other components to
communicate with each others.

Error handling
--------------
When there is a Ctrl-C the agent should kill all other components and
disconnect as gracefully as possible.


Serial mode (with 802.15.4 probe)
---------------------------------
The following diagram describes how the agent the interfaces and
interactions using serial mode (--serial option)

TODO:
add link to source code for probe

**IMPORTANT**:
This mode of functioning assumes the following IEEE802.15.4 settings:

1. Channel, modulation, data-rate (Channels 11-26 at 2.4 GHz).
2. MAC mode is beaconless.
3. Security is off


# Agent combined with active-probe
----------------------------------
This mode can be used for connecting two remote (geographically distant)
802.15.4 based devices.

Active mode probe automatically ACKs messages received by the user
device, the 802.15.4 are not forwarded to the AMQP connection.

## Running the agent
export AMQP connection variables, and USB params for the serial connection

env vars:
`
export AMQP_EXCHANGE='amq.topic'
export AMQP_URL="amqp://someUser:somePassword@f-interop.rennes.inria.fr/sessionXX"
`

check usb port, with for example with `ls /dev/tty*`

`
export FINTEROP_CONNECTOR_SERIAL_PORT=/dev/tty.XXX
export FINTEROP_CONNECTOR_BAUDRATE=115200
`

then execute (e.g. for a coap_server running under the agent):
`
python -m agent connect  --url $AMQP_URL --name coap_server --serial
`

```

                           +----------------+
                           |                |
                           |   AMQP broker  |
                           |                |
                           |                |
                           +----------------+


                                 ^     +
                                 |     |
data.serial.fromAgent.agent_name |     | data.serial.toAgent.agent_name
                                 |     |
                                 +     v

                           +----------------+
                           |                |
                           |                |
                           |     Agent      |
                           | (serial mode)  |
                           |                |
                           |                |
                           +-------+--------+
                                   | USB interface
                                   | (SLIP protocol)
                           +-------+--------+                        +---------------+
                           |                |     802.15.4 frame     |               |
                           |                |  <-----------------+   |   802.15.4    |
                           |    probe mote  |                        |     user      |
                           |  (active mode) |  +----------------->   |    device     |
                           |                |                        |               |
                           |                |                        |               |
                           +----------------+                        +---------------+
```



# Agent combined with passive-probe
-----------------------------------
This mode can be used for forwarding all sniffed packet in a 802.15.4 network to AMQP broker
and eventually other tools listening to the correct routing keys/topics.

## Running the agent
**TBD**

```

                        +----------------+
                        |                |
                        |   AMQP broker  |
                        |                |
                        |                |
                        +----------------+

                                 ^
                                 |
data.serial.fromAgent.agent_name |
                                 |
                                 +

                         +----------------+
                         |                |
                         |                |
                         |     Agent      |
                         | (serial mode)  |
                         |                |
                         |                |
                         +-------+--------+
                                 | USB interface
                                 | (SLIP protocol)
                         +-------+--------+
                         |                |
                         |                |
                         |    probe mote  |
                         |  (passive mode)|
                         |                |
                         |                |
                         +-------+--------+
                                 |
                                 |
                                 |
                                 |
+---------------+                |              +---------------+
|               |                |              |               |
|   802.15.4    |       <--------+--------+     |   802.15.4    |
|     user      |         802.15.4 frames       |     user      |
|    device     |       +----------------->     |    device     |
|               |                               |               |
|               |                               |               |
+---------------+                               +---------------+

```



IP tunneling mode (active-probe)
--------------------------------
This mode can be used for communicating two IPv6-based implementations
tunneling all traffic through AMQP messages.

## Running the agent
For running the agent you will need privileges on the machine, basically
cause we need to open a virtual interface to tunnel the packets.

The command for executing it will be provided to you by the
GUI or AMQP broker sys admin, it should look something like this:

```
sudo python -m agent connect  --url amqp://someUser:somePassword@f-interop.rennes.inria.fr/sessionXX --name coap_client
```

for more info
```
python agent.py --help
python agent.py connect --help
```



```
                          +----------------+
                          |                |
                          |   AMQP broker  |
                          |                |
                          |                |
                          +----------------+


                                ^     +
                                |     |
data.tun.fromAgent.agent_name   |     |  data.tun.toAgent.agent_name
                                |     |
                                +     v

                 +---------------------------------+
                 |                                 |
                 |               Agent             |
                 |                                 |
                 |             (tun mode)          |
                 |                                 |
                 |                                 |
                 |   +------tun interface--------+ |
                 |                                 |
                 |  +----------------------------+ |
                 |  |         IPv6-based         | |
                 |  |        communicating       | |
                 |  |      piece of software     | |
                 |  |      (e.g. coap client)    | |
                 |  |                            | |
                 |  +----------------------------+ |
                 +---------------------------------+

```