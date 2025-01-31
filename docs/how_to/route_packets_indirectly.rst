Route Packets Indirectly
========================

Goal
----
This tutorial demonstrates how to route packets indirectly using the Cubesat Space Protocol (CSP). By setting up routing tables and interfaces, you can control the path packets take through the network.

Explanation
-----------
In CSP.py, routing tables and interfaces are used to manage the flow of packets between nodes. By configuring these components, you can ensure that packets are routed through specific paths, even if they are not directly connected.

Key Components
--------------
1. **CspRoutingTable Class**:
    The ``CspRoutingTable`` class manages the routing entries that determine how packets are forwarded.

    .. code-block:: python

        class CspRoutingTable:
            def __init__(self) -> None:
                self._routes: list[Route] = []

            def add_entry(self, *, network_address: int, netmask_bits: int, iface: ICspInterface) -> None:
                if any(route for route in self._routes if route.network_address == network_address and route.netmask_bits == netmask_bits):
                    raise ValueError('Duplicate route entry')
                self._routes.append(Route(
                    network_address=network_address,
                    netmask_bits=netmask_bits, 
                    iface=iface
                ))

            def iface_for_address(self, address: int) -> ICspInterface | None:
                matching_routes = [route for route in self._routes if route.routes_to_address(address)]
                if len(matching_routes) == 0:
                    return None
                if len(matching_routes) == 1:
                    return matching_routes[0].iface
                matching_routes = list(sorted(matching_routes, key=lambda r: r.netmask_bits, reverse=True))
                return matching_routes[0].iface

2. **CspRouter Class**:
    The ``CspRouter`` class manages the interfaces and routing logic.

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

            def add_interface(self, interface: ICspInterface, *, address: int, netmask_bits: int) -> None:
                iface_address = CspInterfaceAddress(address=address, network_address_bits=netmask_bits)
                self._interfaces.append((iface_address, interface))
                def sink_packet(packet: CspPacket) -> None:
                    self.push_packet(interface, packet)
                interface.set_packet_sink(sink_packet)

            async def send_packet(self, packet: CspPacket) -> None:
                target = self._find_outgoing_interface(packet.packet_id.dst)
                if target is None:
                    raise ValueError("no interface matched the packet destination")
                iface_addr, iface = target
                packet = packet.with_id(packet.packet_id.with_source(iface_addr.address))
                await self._process_outgoing_packet(packet, iface)

            def _find_outgoing_interface(self, target: int) -> tuple[CspInterfaceAddress, ICspInterface] | None:
                ifaces = [(addr, iface) for addr, iface in self._interfaces if addr.contains_address(target)]
                if len(ifaces) == 1:
                    return ifaces[0]
                if len(ifaces) > 1:
                    raise ValueError('More than one interface matched the packet destination')
                iface_by_route = self.rtable.iface_for_address(target)
                if iface_by_route is None:
                    return None
                [iface_addr] = [addr for (addr, iface) in self._interfaces if iface == iface_by_route]
                return iface_addr, iface_by_route

How-to Guide
------------

Setting Up Indirect Routing

1. **Create a CSP Node and Add Interfaces**:
    Initialize a ``CspNode`` instance and add interfaces to it.

    .. code-block:: python

        import asyncio
        import csp_py

        async def main():
            node = csp_py.CspNode()
            lo_interface = csp_py.interfaces.LoInterface()
            node.router.add_interface(lo_interface, address=0, netmask_bits=14)

2. **Add Routing Table Entries**:
    Add entries to the routing table to define indirect routes.

    .. code-block:: python

        node.router.rtable.add_entry(network_address=0x0100, netmask_bits=6, iface=lo_interface)
        node.router.rtable.add_entry(network_address=0x0200, netmask_bits=6, iface=lo_interface)

3. **Send Packets Using Indirect Routes**:
    Use the node to send packets that will be routed indirectly.

    .. code-block:: python

        async def send_packet(node: csp_py.CspNode):
            connection = await node.connect(dst=0x0200, port=10)
            await connection.send(b'Hello, indirect route!')

Example Usage
-------------
Here is an example of how to set up and use indirect routing in a CSP.py complete example application:

.. code-block:: python

    import asyncio
    import csp_py
    from csp_py.interfaces.lo_interface import LoInterface
    from csp_py import CspNode, IPacketHandler


    async def send_packet(node: CspNode):
        connection = await node.connect(dst=0, port=10)
        await connection.send(b'Hello, CSP!')


    async def receive_packet(node: CspNode):
        node.listen(10)


    class MyPacketHandler(IPacketHandler):
        async def on_packet(self, packet):
            print(f'Packet received: {packet.data.decode()}')
            return True


    async def main():
        node = csp_py.CspNode()
        node.add_packet_handler(MyPacketHandler())

        lo_interface = LoInterface()
        node.router.rtable.add_entry(network_address=0x0100, netmask_bits=6, iface=lo_interface)
        node.router.add_interface(lo_interface, address=0x0200, netmask_bits=14)

        router_task = asyncio.create_task(node.router.arun())
        
        received = asyncio.create_task(receive_packet(node))
        await send_packet(node)
        await received

        router_task.cancel()

Summary
-------
By following these steps, you can set up indirect routing in your CSP.py application. This allows you to control the path packets take through the network, ensuring they are routed through specific interfaces and paths.