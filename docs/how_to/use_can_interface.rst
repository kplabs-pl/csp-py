Use CAN interface
=================

Goal
----

This guide will show you how to use the CAN interface in CSP.py. The CAN (Controller Area Network) interface allows microcontrollers and devices to communicate with each other without a host computer. This guide will walk you through setting up and using the CAN interface in your CSP.py application.

Explanation
-----------

The `CspCanInterface` in CSP.py handles communication over a CAN bus. It fragments and reassembles packets to fit within the constraints of CAN frames. This interface is useful for applications that require robust and reliable communication between devices in a network.

Key Components
--------------

1. **CspCanInterface Class**:
    The `CspCanInterface` class manages the fragmentation and reassembly of packets for CAN communication. It includes methods for sending and receiving packets, as well as handling incoming CAN frames.

    .. code-block:: python

        class CspCanInterface(ICspInterface):
            def __init__(self) -> None:
                self._in_flight: dict[Any, CfpReassemblyTracker] = {}
                self._packet_sink: CspPacketSink | None = None
                self._sender_counter = 0
                self.send_can_frame: Callable[[int, bytes], Awaitable[None]] | None = None

            def set_packet_sink(self, sink: CspPacketSink) -> None:
                self._packet_sink = sink

            async def send(self, packet: CspPacket) -> None:
                data = packet.data
                fragments = []
                fragments.append(data[:4])
                data = data[4:]
                while len(data) > 0:
                    fragments.append(data[:8])
                    data = data[8:]
                if len(fragments) == 1:
                    await self._send_singleton_frame(packet)
                else:
                    await self._send_multi_frame(packet, fragments)

            async def on_can_frame(self, can_id: int, data: bytes) -> None:
                parsed_id = parse_csp_can_frame_id(can_id)
                key = parsed_id.as_key()
                if parsed_id.begin:
                    if len(data) < 4:
                        print('[csp.py] Invalid data length')
                        return
                    header, data = parse_csp_can_header(data)
                    self._in_flight[key] = CfpReassemblyTracker(parsed_id, header)
                self._in_flight[key].append(data)
                if parsed_id.end:
                    full_packet = self._in_flight.pop(key).capture()
                    assert self._packet_sink is not None
                    self._packet_sink(full_packet)

2. **Adding the CAN Interface**:
    The CAN interface is added to the router using the `add_interface` method. Each interface is associated with an address and a network mask.

    .. code-block:: python

        node.router.add_interface(can_interface, address=0x100, netmask_bits=14)

3. **Sending and Receiving Packets**:
    Use the CAN interface to send and receive packets. The interface handles the fragmentation and reassembly of packets to fit within CAN frames.

    .. code-block:: python

        async def send_packet(node: CspNode):
            connection = await node.connect(dst=0x200, port=10)
            await connection.send(b'Hello, CAN!')

        async def receive_packet(node: CspNode):
            socket = node.listen(10)
            connection = await socket.accept()
            packet = await connection.recv()
            print(f'Received: {packet.data.decode()}')

Example Usage
-------------

Here is an example of how to use the CAN interface in a CSP.py application:

1. **Set Up the Application Skeleton**:
    .. code-block:: python

        import asyncio
        import csp_py
        from csp_py.interfaces.can import CspCanInterface


        async def main():
            node = csp_py.CspNode()

            can_interface = CspCanInterface()
            can_interface.send_can_frame = lambda can_id, data: asyncio.create_task(can_interface.on_can_frame(can_id, data))
            node.router.add_interface(can_interface, address=0x100, netmask_bits=14)

            router_task = asyncio.create_task(node.router.arun())

            received = asyncio.create_task(receive_packet(node))

            await send_packet(node)

            await received

            router_task.cancel()

        asyncio.run(main())

In the code snippet above, we create a `CspNode` instance and add a `CspCanInterface` to it. We then set up tasks to send and receive packets using the CAN interface.

2. **Send and Receive Packets**:
    .. code-block:: python

        async def send_packet(node: csp_py.CspNode):
            connection = await node.connect(dst=0x100, port=10)
            await connection.send(b'Hello, CAN!')

        async def receive_packet(node: csp_py.CspNode):
            socket = node.listen(10)
            connection = await socket.accept()
            packet = await connection.recv()
            print(f'Received: {packet.data.decode()}')

Here we extend the code with the `send_packet` and `receive_packet` functions to send and receive packets using the CAN interface. The `send_packet` function sends a packet to the address `0x100`, while the `receive_packet` function listens for incoming packets on port `10`.

Summary
-------

By following these steps, you can set up and use the CAN interface in your CSP.py application. This allows you to leverage the robust and reliable communication capabilities of the CAN bus for your projects.