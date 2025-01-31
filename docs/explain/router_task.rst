Router Task
===========

In CSP.py, the router task is a main component responsible for managing the routing of packets between different interfaces and ensuring that packets reach their intended destinations. The router task operates asynchronously, processing incoming packets and determining the appropriate actions based on the packet's destination.

Understanding the Router Task
-----------------------------

The router task in CSP.py is responsible for handling the following key functions:

1. **Processing Incoming Packets**:
    The router task continuously processes incoming packets from various interfaces. It determines whether the packet is destined for the local node or needs to be routed to another interface.

2. **Routing Packets**:
    If a packet is not destined for the local node, the router task identifies the appropriate outgoing interface and forwards the packet accordingly.

3. **Applying Filters**:
    The router task can apply various filters to incoming, routed, and outgoing packets. These filters can modify or drop packets based on specific criteria.

Key Components
--------------

1. **CspRouter Class**:
    The ``CspRouter`` class is the core component of the router task. It manages the interfaces, routing table, and packet processing logic.

    .. code-block:: python

        class CspRouter:
            def __init__(self) -> None:
                self._interfaces: list[tuple[CspInterfaceAddress, ICspInterface]] = []
                self._incoming_packets = asyncio.Queue[tuple[ICspInterface, CspPacket]]()
                self.rtable = CspRoutingTable()
                self.local_packet_handler: Callable[[CspPacket], Awaitable[None]] | None = None

                self.incoming_packet_filters: list[CspRouterFilter] = []
                self.routed_packet_filters: list[CspRouterFilter] = []
                self.outgoing_packet_filters: list[CspRouterFilter] = []

2. **Adding Interfaces**:
    Interfaces are added to the router using the ``add_interface`` method. Each interface is associated with an address and a network mask.

    .. code-block:: python

        def add_interface(self, interface: ICspInterface, *, address: int, netmask_bits: int) -> None:
            iface_address = CspInterfaceAddress(address=address, network_address_bits=netmask_bits)
            self._interfaces.append((iface_address, interface))

            def sink_packet(packet: CspPacket) -> None:
                self.push_packet(interface, packet)

            interface.set_packet_sink(sink_packet)

3. **Processing Packets**:
    The router task processes incoming packets by determining their destination and taking appropriate actions. If the packet is destined for the local node, it is processed locally. Otherwise, it is routed to the appropriate outgoing interface.

    .. code-block:: python

        async def process_one_incoming_packet(self) -> None:
            src_iface, packet = await self._incoming_packets.get()

            [src_address] = [addr for addr, iface in self._interfaces if iface == src_iface]

            to_localhost = packet.packet_id.dst in [src_address.address, src_address.broadcast_address]
            if to_localhost:
                await self._process_incoming_packet(packet)
                return
            
            target = self._find_outgoing_interface(packet.packet_id.dst)

            if target is None:
                return
            
            target_address, target_iface = target

            if target_iface == src_iface:
                return

            if target_address.address == packet.packet_id.dst:
                return

            await self._process_routed_packet(packet, target_iface)

4. **Sending Packets**:
    The router task sends packets by determining the appropriate outgoing interface and applying any necessary filters.

    .. code-block:: python

        async def send_packet(self, packet: CspPacket) -> None:
            target = self._find_outgoing_interface(packet.packet_id.dst)
            
            if target is None:
                raise ValueError("no interface matched the packet destination")
            
            iface_addr, iface = target

            packet = packet.with_id(packet.packet_id.with_source(iface_addr.address))
            await self._process_outgoing_packet(packet, iface)

Example Usage
-------------

Here is an example of how the router task might be used in a CSP.py application:

1. **Creating a Node**:
    First, create a CSP node and start the router task.

    .. code-block:: python

        import asyncio
        import csp_py

        async def main():
            node = csp_py.CspNode()
            router_task = asyncio.create_task(node.router.arun())

2. **Adding Interfaces**:
    Add interfaces to the router to enable communication between different nodes.

    .. code-block:: python

        lo_interface = csp_py.interfaces.LoInterface()
        node.router.add_interface(lo_interface, address=0, netmask_bits=14)

3. **Sending and Receiving Packets**:
    Use the node to send and receive packets, leveraging the router task to manage packet routing.

    .. code-block:: python

        async def send_and_receive(node: csp_py.CspNode):
            connection = await node.connect(dst=0, port=10)
            await connection.send(b'Hello, CSP!')
            response = await connection.recv()
            print(f'Received: {response.data.decode()}')

        asyncio.run(send_and_receive(node))
