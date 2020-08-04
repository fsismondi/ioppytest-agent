Agent for ioppytest framework 
-----------------------------

About
-----
Agent (~VPN client) is a component of the ioppytest framework ecosystem which creates tunnels between the IUTs,
or between IUT and test system.

The following diagram described the resulting network connection between implementations:

```
+--------------------------------+                                             +--------------------------------+
|  +--------------------------+  |                                             |  +--------------------------+  |
|  |              |           |  |                                             |  |              |           |  |
|  |     IUT      |   ping    |  |                                             |  |     IUT      |   ping    |  |
|  |              |           |  |                                             |  |              |           |  |
|  |              |           |  | PC 1                                  PC 2  |  |              |           |  |
|  +--------------------------+  |                                             |  +--------------------------+  |
|  |          tun0            |  |                                             |  |          tun0            |  |
|  |                          |  |                                             |  |                          |  |
|  |  virtual ip  10.2.0.1    |  |                                             |  |  virtual ip  10.2.0.2    |  |
|  |  addresses:  bbbb::1     |  |                                             |  |  addresses:  bbbb::2     |  |
|  |                          |  |                                             |  |                          |  |
|  +--------------------------+  |                                             |  +--------------------------+  |
|  |          agent_1         |  | +-----------------------------------------> |  |          agent_2         |  |
|  |        (VPN client)      |  |         transport  (ip over foo)            |  |        (VPN client)      |  |
|  +--------------------------+  | <-----------------------------------------+ |  +--------------------------+  |
+--------------------------------+                                             +--------------------------------+

```

The agent components needs to run in the user's host. 
It builds a virtual interface for enabling the communication, same way openVPN does.
The previous diagram show a two IUT network build with the agent, but the network can support any number agents.


Error handling
--------------
When there is a user interrupt signal (Ctrl-C) the agent should all running threads and should gracefully disconnect.


Running the agent
-----------------

For running the agent you will need privileges on the machine, basically
cause we need to open a virtual interface to tunnel the packets.

The command for executing it will be provided to you by the
GUI or AMQP broker sys admin, it should look something like this:

```
sudo python -m agent connect  --url amqp://someUser:somePassword@f-interop.rennes.inria.fr/sessionXX --name agent_x
```

for more info

```
python agent.py --help
python agent.py connect --help
```


AMQP as IP packet transport 
---------------------------

IP packets sent to the virtual interface will be encapsulated in AQMP messages and sent over the event bus.
This messages are then forwarded to the corresponding agent.
The routing between the agents is automagically hanlded by the packet router.

```
    +--------------------------------+                                          +--------------------------------+
    |  +--------------------------+  |                                          |  +--------------------------+  |
    |  |              |           |  |                                          |  |              |           |  |
    |  |    oneM2M    |  ping     |  |                                          |  |    oneM2M    |  ping     |  |
    |  |     IUT      |           |  |                                          |  |     IUT      |           |  |
    |  |              |           |  |  +----------------------------+          |  |              |           |  |
    |  +--------------------------+  |  |                            |          |  +--------------------------+  |
    |  |          tun0            |  |  |                            |          |  |          tun0            |  |
    |  |                          |  |  |       Packet Router        |          |  |                          |  |
    |  |  virtual ip  10.2.0.1    |  |  |    (forwards amqp messages)|          |  |  virtual ip  10.2.0.2    |  |
    |  |  addresses:  bbbb::1     |  |  |                            |          |  |  addresses:  bbbb::2     |  |
    |  |                          |  |  +----------------------------+          |  |                          |  |
    |  +--------------------------+  |                                          |  +--------------------------+  |
    |  |          agent_1         |  |              ^    +                      |  |          agent_2         |  |
    |  |        (VPN client)      |  |              |    |                      |  |        (VPN client)      |  |
    |  +--------------------------+  |              |    |                      |  +--------------------------+  |
    +--------------------------------+              |    |                      +--------------------------------+
                                                    |    |
                 +     ^                            |    |                                      ^     +
                 |     |                        1,3 |    | 2,4                                  |     |
               1 |     | 2                          |    |                                    4 |     | 3
                 |     |                            |    |                                      |     |
                 v     +                            +    v                                      +     v

 +----------------------------------------------------------------------------------------------------------------->
                                            AMQP Event Bus
 <-----------------------------------------------------------------------------------------------------------------+


AMQP Topics:
1=fromAgent.agent_1_name.ip.tun.packet.raw
2=toAgent.agent_1_name.ip.tun.packet.raw
3=fromAgent.agent_2_name.ip.tun.packet.raw
4=toAgent.agent_2_name.ip.tun.packet.raw

```


