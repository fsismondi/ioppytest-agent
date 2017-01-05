Agent for the f-interop platform
#################################


Design
------

The design of the f-interop agent is modular by design.
An agent is made of different processes that connect and exchange messages to each others
using ZMQ sockets.

Core
----

When started, the agent starts up the core module. This component is in charge of launching
all the other components. If new components needs to be added they just need to be launched
from this component.

Core open the default ZMQ socket that is used by other components to communicate with each others.

Error handling
--------------

When there is a Ctrl-C the agent should kill all other components and disconnect as gracefully as possible.
