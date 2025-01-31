Interfaces
==========

In CSP.py, interfaces are essential components that enable communication between different nodes in a network.
They are responsible for sending and receiving packets over various communication mediums.

Understanding Interfaces
------------------------

An interface in CSP.py is responsible for handling the transmission and reception of packets over a specific medium. This could be for example a CAN interface, or any other type of communication interface.
The primary role of an interface is to act as a conduit for packets, ensuring they are correctly transmitted to their destination and received from the source.

Every interface is associated with a specific network address and bitmask. 

When a packet is transmitted (received or sent) the ``CspRouter`` will find the interface that matches the destination address of the packet. 
The interface will then handle the transmission of the packet.

.. note::
    Keep in mind that each destination address can be associated only with one interface.

    During the routing process, if the router finds multiple interfaces that match the destination address, it will raise an error.
