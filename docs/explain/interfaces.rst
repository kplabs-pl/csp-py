Interfaces
==========

In CSP.py, interfaces are essential components that enable communication between different nodes in a network. Each interface follows a specific protocol to send and receive packets. Let's break down the key concepts and components involved in CSP.py interfaces.

Understanding Interfaces
------------------------

An interface in CSP.py is responsible for handling the transmission and reception of packets over a specific medium. This could be a loopback interface, a CAN interface, or any other type of communication interface. The primary role of an interface is to act as a conduit for packets, ensuring they are correctly transmitted to their destination and received from the source.

Key Components
--------------

1. **ICspInterface Protocol**:
    The `ICspInterface` protocol defines the blueprint for all interfaces in CSP.py. It includes two essential methods:
    
    - `set_packet_sink(self, sink: CspPacketSink) -> None`: This method sets the packet sink, which is a callback function that processes incoming packets.
    - `async def send(self, packet: CspPacket) -> None`: This method is responsible for sending a packet through the interface.

LoInterface
-----------

The `LoInterface` is a loopback interface in CSP.py. It is designed to send packets back to the local node, making it useful for testing and local communication. Let's break down how the `LoInterface` works and its key components.

1. **Initialization**:
    The `LoInterface` class is initialized without any parameters. During initialization, it sets up an internal variable `_packet_sink` to `None`. This variable will later hold the callback function that processes incoming packets.

    .. code-block:: python

        class LoInterface(ICspInterface):
            def __init__(self) -> None:
                super().__init__()
                self._packet_sink: CspPacketSink | None = None

2. **Setting the Packet Sink**:
    The `set_packet_sink` method is used to set the packet sink. The packet sink is a callback function that processes incoming packets. This method assigns the provided `sink` function to the `_packet_sink` variable.

    .. code-block:: python

        def set_packet_sink(self, sink: CspPacketSink) -> None:
            self._packet_sink = sink

3. **Sending Packets**:
    The `send` method is responsible for sending packets through the interface. In the case of `LoInterface`, this method simply calls the packet sink with the provided packet. This effectively "loops" the packet back to the local node.

    .. code-block:: python

        async def send(self, packet: CspPacket) -> None:
            sink = self._packet_sink
            assert sink is not None
            sink(packet)

Example Usage
-------------

Here is an example of how the `LoInterface` might be used in a CSP.py application:

1. **Creating a Node**:
    First, create a CSP node and add the `LoInterface` to it.

    .. code-block:: python

        import asyncio
        import csp_py

        async def main():
            node = csp_py.CspNode()
            lo_interface = csp_py.interfaces.LoInterface()
            node.router.add_interface(lo_interface, address=0, netmask_bits=14)

2. **Sending and Receiving Packets**:
    Next, set up a task to send a packet through the `LoInterface` and handle the received packet.

    .. code-block:: python

        async def send_and_receive(node: csp_py.CspNode):
            connection = await node.connect(dst=0, port=10)
            await connection.send(b'Hello, loopback!')
            response = await connection.recv()
            print(f'Received: {response.data.decode()}')

        asyncio.run(send_and_receive(node))

In this example, the packet sent through the `LoInterface` is immediately received back by the same node, demonstrating the loopback functionality.

CspSerializingInterface
-----------------------

The `CspSerializingInterface` is responsible for converting packets to and from a byte stream format suitable for transmission over a communication medium. It serializes packets before sending them and deserializes incoming byte streams back into packets.

1. **Initialization**:
    The `CspSerializingInterface` class is initialized with a callback function `on_frame` that handles the serialized frames. It also sets up an internal variable `_packet_sink` to `None`.

    .. code-block:: python

        class CspSerializingInterface(ICspInterface):
            def __init__(self, on_frame: SerializedFrameSink) -> None:
                self._frame_sink = on_frame
                self._packet_sink: CspPacketSink | None = None

2. **Setting the Packet Sink**:
    Similar to `LoInterface`, the `set_packet_sink` method sets the packet sink callback function.

    .. code-block:: python

        def set_packet_sink(self, sink: CspPacketSink) -> None:
            self._packet_sink = sink

3. **Sending Packets**:
    The `send` method serializes the packet into a byte stream and then calls the frame sink callback function to handle the serialized frame.

    .. code-block:: python

        async def send(self, packet: CspPacket) -> None:
            header_num = CspIdLayout.to_int(packet.packet_id)
            header = struct.pack('!Q', header_num)[2:]
            frame = header + packet.data
            await self._frame_sink(frame)

4. **Handling Incoming Frames**:
    The `on_incoming_frame` method deserializes the incoming byte stream back into a packet and then calls the packet sink callback function.

    .. code-block:: python

        async def on_incoming_frame(self, frame: bytes) -> None:
            header = b'\x00\x00' + frame[:6]
            payload = frame[6:]
            header_num, = struct.unpack('!Q', header)
            incoming_id = CspIdLayout.from_int(header_num)
            packet = CspPacket(
                packet_id=incoming_id,
                data=payload,
            )
            sink = self._packet_sink
            assert sink is not None
            sink(packet)

CspCanInterface
---------------

The `CspCanInterface` handles communication over a CAN bus. CAN (Controller Area Network) is a robust vehicle bus standard designed to allow microcontrollers and devices to communicate with each other without a host computer. This interface fragments and reassembles packets to fit within the constraints of CAN frames.

1. **Initialization**:
    The `CspCanInterface` class initializes internal variables to manage packet reassembly and the packet sink.

    .. code-block:: python

        class CspCanInterface(ICspInterface):
            def __init__(self) -> None:
                self._in_flight: dict[Any, CfpReassemblyTracker] = {}
                self._packet_sink: CspPacketSink | None = None
                self._sender_counter = 0
                self.send_can_frame: Callable[[int, bytes], Awaitable[None]] | None = None

2. **Setting the Packet Sink**:
    The `set_packet_sink` method sets the packet sink callback function.

    .. code-block:: python

        def set_packet_sink(self, sink: CspPacketSink) -> None:
            self._packet_sink = sink

3. **Sending Packets**:
    The `send` method fragments the packet into smaller frames suitable for CAN transmission and sends each frame.

    .. code-block:: python

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

4. **Handling Incoming Frames**:
    The `on_can_frame` method reassembles incoming frames into a complete packet and then calls the packet sink callback function.

    .. code-block:: python

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

Conclusion
----------

Interfaces in CSP.py are essential for enabling communication between nodes. By implementing the `ICspInterface` protocol, different types of interfaces can be created to handle various communication mediums. Understanding how these interfaces work and how they are implemented is crucial for effectively using CSP.py in your projects.