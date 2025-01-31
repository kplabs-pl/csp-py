Limit packet size using filters
===============================

Goal
----

This guide will show you how to limit the packet size using filters in CSP.py. By applying filters, you can ensure that packets exceeding a certain size are either truncated or dropped, depending on your requirements.

Explanation
-----------

Filters in CSP.py allow you to process, modify, or drop packets as they are routed through the system. By using filters, you can enforce a maximum packet size, ensuring that packets exceeding this size are handled appropriately.

Key Components
--------------

1. **CspRouter Class**:
    The `CspRouter` class manages the interfaces, routing table, and packet processing logic. It includes lists for incoming, routed, and outgoing packet filters.

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
    Filters are registered by appending them to the appropriate filter list in the `CspRouter` instance.

    .. code-block:: python

        router.incoming_packet_filters.append(incoming_filter)
        router.outgoing_packet_filters.append(outgoing_filter)

3. **Applying Filters**:
    Filters are applied to packets during the routing process. Each filter can modify the packet or drop it by returning `None`.

    .. code-block:: python

        async def _process_incoming_packet(self, packet: CspPacket) -> None:
            for f in self.incoming_packet_filters:
                filter_result = await f(packet)
                if filter_result is None:
                    return
                packet = filter_result
            await self._on_packet_to_local(packet)

How-to Guide
------------

Limiting Packet Size

1. **Define the Maximum Packet Size**:
    Set the maximum packet size that you want to enforce.

    .. code-block:: python

        MAX_PACKET_SIZE = 256  # Example size in bytes

2. **Define the Incoming and Outgoing Filters**:
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

3. **Register the Filters with the Router**:
    Register the filters with the `CspRouter` instance to apply them to incoming and outgoing packets.

    .. code-block:: python

        def register_size_limit_filters(router: CspRouter) -> None:
            router.incoming_packet_filters.append(incoming_filter)
            router.outgoing_packet_filters.append(outgoing_filter)

4. **Use the Filters in Your Node**:
    Register the size limit filters in your CSP node.

    .. code-block:: python

        node = CspNode()
        register_size_limit_filters(node.router)

Example Usage
-------------

Here is an example of how to use the size limit filters in a CSP.py application:

1. **Set Up the Application Skeleton**:
    .. code-block:: python

        import asyncio
        import csp_py

        async def main():
            node = csp_py.CspNode()
            register_size_limit_filters(node.router)
            router = asyncio.create_task(node.router.arun())
            server = asyncio.create_task(server_task(node))
            client = asyncio.create_task(client_task(node))
            await client
            server.cancel()
            router.cancel()

        asyncio.run(main())

2. **Define the Client Task**:
    .. code-block:: python

        async def client_task(node: csp_py.CspNode):
            connection = await node.connect(dst=0, port=20)
            for i in range(0, 10):
                data = f'Hello, world! {i}'.encode('utf-8')
                if len(data) <= MAX_PACKET_SIZE:
                    await connection.send(data)
                response = await connection.recv()
                print(f'Got response: {response.data.decode('utf-8')}')

3. **Define the Server Task**:
    .. code-block:: python

        async def server_task(node: csp_py.CspNode):
            socket = node.listen(20)
            while True:
                connection = await socket.accept()
                while True:
                    packet = await connection.recv()
                    await connection.send(b'Response to ' + packet.data)

Summary
-------

By following these steps, you can enforce a maximum packet size in your CSP.py application using filters. This ensures that packets exceeding the specified size are appropriately handled, either by truncating or dropping them.