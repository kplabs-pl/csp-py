Use serializing interface
=========================

Goal
----

This guide will show you how to use the serializing interface in CSP.py. The ``CspSerializingInterface`` is responsible for converting packets to and from a byte stream format suitable for transmission over a communication medium. This guide will walk you through setting up and using the serializing interface in your CSP.py application.

Explanation
-----------

The ``CspSerializingInterface`` in CSP.py handles the serialization and deserialization of packets. It converts packets into a byte stream before sending them and converts incoming byte streams back into packets. This interface is useful for communication over mediums that require a specific byte stream format.

Key Components
--------------

1. **CspSerializingInterface Class**:
    The ``CspSerializingInterface`` class manages the serialization and deserialization of packets. It includes methods for sending packets as byte streams and handling incoming byte streams.

    .. code-block:: python

        class CspSerializingInterface(ICspInterface):
            def __init__(self, on_frame: SerializedFrameSink) -> None:
                self._frame_sink = on_frame
                self._packet_sink: CspPacketSink | None = None

            def set_packet_sink(self, sink: CspPacketSink) -> None:
                self._packet_sink = sink

            async def send(self, packet: CspPacket) -> None:
                header_num = CspIdLayout.to_int(packet.packet_id)
                header = struct.pack('!Q', header_num)[2:]
                frame = header + packet.data
                await self._frame_sink(frame)

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

2. **Setting the Packet Sink**:
    The ``set_packet_sink`` method sets the packet sink callback function, which processes incoming packets.

    .. code-block:: python

        def set_packet_sink(self, sink: CspPacketSink) -> None:
            self._packet_sink = sink

3. **Sending Packets**:
    The ``send`` method serializes the packet into a byte stream and then calls the frame sink callback function to handle the serialized frame.

    .. code-block:: python

        async def send(self, packet: CspPacket) -> None:
            header_num = CspIdLayout.to_int(packet.packet_id)
            header = struct.pack('!Q', header_num)[2:]
            frame = header + packet.data
            await self._frame_sink(frame)

4. **Handling Incoming Frames**:
    The ``on_incoming_frame`` method deserializes the incoming byte stream back into a packet and then calls the packet sink callback function.

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

Example Usage
-------------

Here is an example of how to use the serializing interface in a CSP.py application:

1. **Set Up the Application Skeleton**:
    .. code-block:: python

        import asyncio
        import csp_py
        from csp_py.interfaces.serializing_interface import CspSerializingInterface


        async def main():
            async def capture_frame(frame: bytes) -> None:
                print(f'Serialized frame: header = {frame[:6]}, data = {frame[6:]}')

            node = csp_py.CspNode()

            serializing_interface = CspSerializingInterface(capture_frame)
            node.router.add_interface(serializing_interface, address=0x100, netmask_bits=14)

            router_task = asyncio.create_task(node.router.arun())
            
            await send_packet(node)

            router_task.cancel()

        asyncio.run(main())

In the code snippet above, we create a ``CspNode`` instance and add a ``CspSerializingInterface`` to it. We then set up a task to send a packet using the serializing interface.
Function ``capture_frame`` is a callback function that prints the serialized frame.

2. **Send Packets**:
    .. code-block:: python

        async def send_packet(node: csp_py.CspNode):
            connection = await node.connect(dst=0x100, port=10)
            await connection.send(b'Hello, serializing interface!')

We can now send packets using the serializing interface.

Summary
-------

By following these steps, you can set up and use the serializing interface in your CSP.py application. This allows you to leverage the serialization and deserialization capabilities of the ``CspSerializingInterface`` for communication over various mediums.