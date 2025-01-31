Limit packet size using filters
===============================

This guide will show you how to limit the packet size using filters in CSP.py. By applying filters, you can ensure that packets exceeding a certain size are either truncated or dropped, depending on your requirements.

Prerequisites
-------------

- Basic tutorial completed (:ref:`simple_server_client`)

Steps
-----

1. **Define the maximum packet size.**
    .. code-block:: python

        MAX_PACKET_SIZE = 256  # Example size in bytes

2. **Define the Incoming and Outgoing Filters**
    Create filters to enforce the maximum packet size. These filters will drop packets that exceed the specified size.

    .. code-block:: python

        async def incoming_filter(packet: CspPacket) -> CspPacket | None:
            if len(packet.data) > MAX_PACKET_SIZE:
                return None  # Drop the packet
            return packet

        async def outgoing_filter(packet: CspPacket) -> CspPacket | None:
            if len(packet.data) > MAX_PACKET_SIZE:
                return None  # Drop the packet
            return packet

3. **Register the Filters**
    Register the filters in the ``CspRouter`` instance inside node to apply them to incoming and outgoing packets.

    .. code-block:: python
        
        # Node initialization

        router = node.router

        router.incoming_packet_filters.append(incoming_filter)
        router.outgoing_packet_filters.append(outgoing_filter)

Now the router will apply these filters to incoming and outgoing packets, ensuring that packets exceeding the specified size are dropped.