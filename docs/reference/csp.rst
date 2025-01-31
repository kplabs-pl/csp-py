CSP.py Reference
================

Overview
--------

CSP.py is a native Python implementation of the Cubesat Space Protocol (CSP). It provides a set of classes and functions to facilitate communication between nodes in a network using CSP. This reference guide covers the key components and their usage.

Classes

CspNode
-------

The ``CspNode`` class represents a node in the CSP network. It is responsible for managing interfaces, routing packets, and handling connections.

**Initialization:**

.. code-block:: python

    node = csp_py.CspNode(default_send_flags=CspPacketFlags.Zero)

**Methods:**

- ``add_packet_handler(handler: IPacketHandler) -> None``: Adds a packet handler to the node.
- ``bound_socket(port: int | None, *, send_flags: CspPacketFlags=CspPacketFlags.Inherit) -> CspBoundSocket``: Creates a bound socket.
- ``listen(port: int | None, *, send_flags: CspPacketFlags=CspPacketFlags.Inherit) -> CspListeningSocket``: Opens a listening socket.
- ``connect(*, dst: int, port: int, local_port: int | None = None, send_flags: CspPacketFlags=CspPacketFlags.Inherit) -> CspClientConnection``: Establishes a connection to a remote node.

IPacketHandler
--------------

The ``IPacketHandler`` interface defines the methods that a packet handler must implement.

**Methods:**

- ``on_packet(packet: CspPacket) -> bool``: `(abstract)` Handles an incoming packet.

CspClientConnection
-------------------

The ``CspClientConnection`` class represents a client connection in the CSP network.

**Initialization:**

.. code-block:: python

    connection = CspClientConnection(socket, remote_address, remote_port)

**Methods:**

- ``send(data: bytes) -> None``: Sends data to the remote node.
- ``recv() -> CspPacket``: Receives data from the remote node.
- ``close() -> None``: Closes the connection.

CspServerConnection
-------------------

The ``CspServerConnection`` class represents a server connection in the CSP network.

**Initialization:**

.. code-block:: python

    connection = CspServerConnection(owner, dst, port, local_port)

**Methods:**

- ``send(data: bytes) -> None``: Sends data to the remote node.
- ``recv() -> CspPacket``: Receives data from the remote node.
- ``close() -> None``: Closes the connection.

CspRouter
---------

The ``CspRouter`` class manages the routing of packets between different interfaces.

**Initialization:**

.. code-block:: python

    router = CspRouter()

**Methods:**

- ``push_packet(iface: ICspInterface, packet: CspPacket) -> None``: Pushes a packet to the router.
- ``arun() -> None``: Asynchronously runs the router task.
- ``process_one_incoming_packet() -> None``: Processes one incoming packet.
- ``add_interface(iface: ICspInterface, *, address: int, netmask_bits: int) -> None``: Adds an interface to the router.
- ``send_packet(packet: CspPacket) -> None``: Processes outgoing packets.

CspRoutingTable
---------------

The ``CspRoutingTable`` class manages routing entries.

**Initialization:**

.. code-block:: python

    rtable = CspRoutingTable()

**Methods:**

- ``add_entry(network_address: int, netmask_bits: int, iface: ICspInterface) -> None``: Adds a routing entry.
- ``iface_for_address(address: int) -> ICspInterface | None``: Finds the interface for a given address.

CspCanInterface
---------------

The ``CspCanInterface`` class handles communication over a CAN bus.

**Initialization:**

.. code-block:: python

    can_interface = CspCanInterface()

**Methods:**

- ``set_packet_sink(sink: CspPacketSink) -> None``: Sets the packet sink.
- ``send(packet: CspPacket) -> None``: Sends a packet.
- ``on_can_frame(can_id: int, data: bytes) -> None``: Handles an incoming CAN frame.

Functions
---------

``parse_csp_can_frame_id``

Parses a CAN frame ID into its components.

**Usage:**

.. code-block:: python

    fields = parse_csp_can_frame_id(can_id)

``parse_csp_can_header``

Parses a CAN header from a byte stream.

**Usage:**

.. code-block:: python

    header, data = parse_csp_can_header(data)

``register_crc32_filters``

Registers CRC32 filters with the router.

**Usage:**

.. code-block:: python

    register_crc32_filters(router)

ping

Sends a ping request to a remote node.

**Usage:**

.. code-block:: python

    response = await ping(node, dst)

Constants
---------

``CspPacketFlags``

Defines flags for CSP packets.

- ``Zero``: No flags.
- ``Inherit``: Inherit flags from the parent packet.
- ``CRC32``: Use CRC32 for error checking.

``CspPacketPriority``

Defines priorities for CSP packets.

- ``Critical``: Critical priority.
- ``High``: High priority.
- ``Normal``: Normal priority.
- ``Low``: Low priority.
 
Dataclasses
-----------

``CspId``

Represents a CSP ID.

**Fields:**

- ``src: int``: Source address.
- ``dst: int``: Destination address.
- ``dport: int``: Destination port.
- ``sport: int``: Source port.
- ``flags: CspPacketFlags``: Packet flags.
- ``priority: CspPacketPriority``: Packet priority.

``CspPacket``

Represents a CSP packet.

**Fields:**

- ``packet_id: CspId``: Packet ID.
- ``header: bytes``: Packet header.
- ``data: bytes``: Packet data.
