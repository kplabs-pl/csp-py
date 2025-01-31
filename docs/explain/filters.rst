Filters
=======

Explanation
-----------

Filters in CSP.py are mechanisms that allow you to process, modify, or drop packets as they are routed through the system. Filters can be applied to incoming, routed, and outgoing packets, providing a flexible way to handle packet processing based on specific criteria.

User can create custom filters to perform tasks such as checksum validation, encryption, or logging. Filters are registered with the ``CspRouter`` instance and applied to packets during the routing process.

Key Components
--------------

1. **CspRouter Class**:
    The ``CspRouter`` class manages the interfaces, routing table, and packet processing logic. It includes lists for incoming, routed, and outgoing packet filters.

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

2. **Registering Filters**:
    Filters are registered by appending them to the appropriate filter list in the ``CspRouter`` instance.

    .. code-block:: python

        router.incoming_packet_filters.append(incoming_filter)
        router.outgoing_packet_filters.append(outgoing_filter)

3. **Applying Filters**:
    Filters are applied to packets during the routing process. Each filter can modify the packet or drop it by returning ``None``.

    .. code-block:: python

        async def _process_incoming_packet(self, packet: CspPacket) -> None:
            for f in self.incoming_packet_filters:
                filter_result = await f(packet)
                if filter_result is None:
                    return
                packet = filter_result
            await self._on_packet_to_local(packet)

5. **The CRC32 Calculation Function**:
    .. code-block:: python

        def calculate_crc32(data: bytes) -> int:
            crc = 0xFFFF_FFFF
            for b in data:
                crc = CRC_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
            return crc ^ 0xFFFF_FFFF

6. **The Incoming and Outgoing Filters**:
    .. code-block:: python

        async def incoming_filter(packet: CspPacket) -> CspPacket | None:
            if (packet.packet_id.flags & 1) == 0:
                return packet

            payload = packet.data[:-4]
            if len(payload) < 4:
                return None

            received_checksum = struct.unpack('!I', packet.data[-4:])[0]
            calculated_checksum = calculate_crc32(payload)
            if received_checksum != calculated_checksum:
                return None

            return packet.with_data(payload)

        async def outgoing_filter(packet: CspPacket) -> CspPacket:
            if (packet.packet_id.flags & 1) == 0:
                return packet

            payload = packet.data
            checksum = calculate_crc32(payload)
            return packet.with_data(payload + struct.pack('!I', checksum))

7. **Registration of the filters with the Router**:
    .. code-block:: python

        router.incoming_packet_filters.append(incoming_filter)
        router.outgoing_packet_filters.append(outgoing_filter)



How-to Guide
------------

Adding a CRC32 Filter to a Node

**Use the Filters in Your Node**:
    .. code-block:: python

        node = CspNode()
        register_crc32_filters(node.router)

Reference
---------

**CspRouter Class**

The ``CspRouter`` class is responsible for managing interfaces, routing tables, and packet processing. It includes methods for adding interfaces, processing packets, and sending packets.

**CspPacket Class**

The ``CspPacket`` class represents a packet in CSP.py. It includes attributes for the packet ID, header, and data.

**CspPacketFlags Enum**

The ``CspPacketFlags`` enum defines flags that can be set on packets, such as ``CRC32`` for enabling CRC32 checksum.

Tutorials
---------
Creating a Simple Server-Client Application with crc32 filters


    .. code-block:: python

        import asyncio
        from csp_py import CspNode, CspPacketFlags, IPacketHandler
        from csp_py.crc32 import register_crc32_filters

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
            node = CspNode(default_send_flags=CspPacketFlags.CRC32)
            register_crc32_filters(node.router)
            router_task = asyncio.create_task(node.router.arun())
            node.add_packet_handler(MyPacketHandler())
            received = asyncio.create_task(receive_packet(node))
            await send_packet(node)
            await received

            router_task.cancel()

Summary
-------

By following these steps, you can create a simple server-client application that uses filters to process packets in CSP.py.