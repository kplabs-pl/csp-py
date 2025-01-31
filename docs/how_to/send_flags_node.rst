Set default flags for outgoing packets
======================================

Goal
----

This guide will show you how to set default flags for outgoing packets in CSP.py. By configuring default flags, you can ensure that all outgoing packets have specific flags set, simplifying the process of packet handling and ensuring consistency.

Explanation
-----------

In CSP.py, the `CspNode` class allows you to set default flags for outgoing packets. These flags are applied to all packets sent from the node unless overridden by specific packet settings. This feature is useful for setting common flags such as CRC32 checksums or other protocol-specific flags.

Key Components
--------------

1. **CspNode Class**:
    The `CspNode` class manages the node's interfaces, routing, and packet handling. It includes an option to set default flags for outgoing packets.

    .. code-block:: python

        class CspNode:
            def __init__(self, *, default_send_flags: CspPacketFlags = CspPacketFlags.Zero) -> None:
                self._default_send_flags = default_send_flags
                self.router = CspRouter()
                self.router.local_packet_handler = self._on_local_packet

                self.router.add_interface(LoInterface(), address=0, netmask_bits=14)

                register_crc32_filters(self.router)

                self._socket_handler = CspSocketHandler()

                self._handlers: list[IPacketHandler] = []

                self.add_packet_handler(CspPingHandler())
                self.add_packet_handler(self._socket_handler)

2. **Setting Default Flags**:
    Default flags are set during the initialization of the `CspNode` instance. These flags are applied to all outgoing packets unless explicitly overridden.

    .. code-block:: python

        node = CspNode(default_send_flags=CspPacketFlags.CRC32)

3. **Resolving Flags**:
    When sending a packet, the node resolves the flags by combining the packet-specific flags with the default flags.

    .. code-block:: python

        async def _send_packet(self, packet: CspPacket) -> None:
            resolved_flags = packet.packet_id.flags.resolve(self._default_send_flags)
            packet = packet.with_id(packet.packet_id.with_flags(resolved_flags))
            await self.router.send_packet(packet)

How-to Guide
------------

Setting Default Flags for Outgoing Packets

1. **Create a CSP Node with Default Flags**:
    Initialize a `CspNode` instance with the desired default flags.

    .. code-block:: python

        node = CspNode(default_send_flags=CspPacketFlags.CRC32)

2. **Send Packets with Default Flags**:
    Use the node to send packets. The default flags will be applied to all outgoing packets.

    .. code-block:: python

        async def send_packet(node: CspNode):
            connection = await node.connect(dst=0, port=10)
            await connection.send(b'Hello, CSP!')

3. **Override Default Flags (Optional)**:
    If needed, you can override the default flags for specific packets by setting the flags explicitly.

    .. code-block:: python

        async def send_packet_with_custom_flags(node: CspNode):
            connection = await node.connect(dst=0, port=10, send_flags=CspPacketFlags.Zero)
            await connection.send(b'Hello, CSP!')

Example Usage
-------------

Here is an example of how to set and use default flags for outgoing packets in a CSP.py application:

1. **Set Up the Application Skeleton**:
    .. code-block:: python

        import asyncio
        import csp_py

        async def main():
            node = csp_py.CspNode(default_send_flags=csp_py.CspPacketFlags.CRC32)
            router_task = asyncio.create_task(node.router.arun())
            await send_packet(node)
            router_task.cancel()

        asyncio.run(main())

2. **Send Packets with Default Flags**:
    .. code-block:: python

        async def send_packet(node: csp_py.CspNode):
            connection = await node.connect(dst=0, port=10)
            await connection.send(b'Hello, CSP!')

Summary
-------

By following these steps, you can set default flags for outgoing packets in your CSP.py application. This ensures that all outgoing packets have the desired flags set, simplifying packet handling and ensuring consistency across your application.