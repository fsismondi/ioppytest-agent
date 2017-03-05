Agent for the f-interop platform
#################################


Design
------

The design of the f-interop agent is modular by design.
An agent is made of different processes that connect and exchange messages to each others
using ZMQ sockets.

Note well
----
Agent is only supported by python2 -> tun librarires py2 only

Running the agent
-----------------
For running the agent you will need privileges on the machine, basically
cause we need to open a virtual interface to tunnel the packets.
The command for executing it will be provided to you by F-Interop web
GUI,it should look something like this:
```
sudo python -m agent connect amqp://finterop.project1.testing:CTT998Y1@f-interop.rennes.inria.fr/4957b25e-4a13-4ef2-9139-6a5313435068#coap_client_agent
```

Core
----

When started, the agent starts up the core module. This component is in charge of launching
all the other components. If new components needs to be added they just need to be launched
from this component.

Core open the default ZMQ socket that is used by other components to communicate with each others.

Error handling
--------------

When there is a Ctrl-C the agent should kill all other components and disconnect as gracefully as possible.
