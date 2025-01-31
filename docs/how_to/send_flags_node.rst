Set default flags for outgoing packets
======================================

This guide will show you how to set default flags for outgoing packets in CSP.py. By configuring default flags, you can ensure that all outgoing packets have specific flags set, simplifying the process of packet handling and ensuring consistency.
In CSP.py, the ``CspNode`` class allows you to set default flags for outgoing packets. These flags are applied to all packets sent from the node unless overridden by specific packet settings. This feature is useful for setting common flags such as CRC32 checksums or other protocol-specific flags.

Prerequisites
-------------

- Basic tutorial completed (:ref:`simple_server_client`)

1. **Setting Default Flags**:
    Default flags are set during the initialization of the ``CspNode`` instance. These flags are applied to all outgoing packets unless explicitly overridden.

    .. code-block:: python

        node = CspNode(default_send_flags=CspPacketFlags.CRC32)

    When sending a packet, the node resolves the flags by combining the packet-specific flags with the default flags.

    .. code-block:: python

        async def _send_packet(self, packet: CspPacket) -> None:
            resolved_flags = packet.packet_id.flags.resolve(self._default_send_flags)
            packet = packet.with_id(packet.packet_id.with_flags(resolved_flags))
            await self.router.send_packet(packet)

2. **Send Packets with Default Flags**:
    Use the node to send packets. The default flags will be applied to all outgoing packets.

    .. code-block:: python

        async def send_packet(node: CspNode):
            connection = await node.connect(dst=0, port=10)
            await connection.send(b'Hello, CSP!')

    Now all packets sent from this connection will have the default flags set.

3. **Override Default Flags (Optional)**:
    If needed, you can override the default flags for specific packets by setting the flags explicitly.

    .. code-block:: python

        async def send_packet_with_custom_flags(node: CspNode):
            connection = await node.connect(dst=0, port=10, send_flags=CspPacketFlags.Zero)
            await connection.send(b'Hello, CSP!')

    When a packet is sent with custom flags defined in the connection, those flags will override the default flags set in the node.