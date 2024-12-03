from csp_py.interfaces.serializing_interface import CspSerializingInterface
from csp_py.packet import CspId, CspPacket, CspPacketPriority


async def test_serialize_outgoing_packet() -> None:
    frames = []
    async def capture_frame(frame: bytes) -> None:
        frames.append(frame)

    iface = CspSerializingInterface(capture_frame)
    await iface.send(CspPacket(
        packet_id=CspId(
            priority=CspPacketPriority.High,
            dst=0x100,
            src=0x200,
            dport=0x13,
            sport=0x34,
        ),
        header=b'header',
        data=b'hello world',
    ))

    assert len(frames) == 1
    assert frames[0] == b'A\x00\x08\x01=\x00hello world'


async def test_deserialize_incoming_packet() -> None:
    packets = []
    def capture_packet(packet: CspPacket) -> None:
        packets.append(packet)

    async def capture_frame(frame: bytes) -> None:
        pass

    iface = CspSerializingInterface(capture_frame)
    iface.set_packet_sink(capture_packet)
    await iface.on_incoming_frame(b'B\x00\x08\x01=\x00hello world')

    assert len(packets) == 1
    assert packets[0] == CspPacket(
        packet_id=CspId(
            priority=CspPacketPriority.High,
            dst=0x200,
            src=0x200,
            dport=0x13,
            sport=0x34,
        ),
        header=b'',
        data=b'hello world',
    )
