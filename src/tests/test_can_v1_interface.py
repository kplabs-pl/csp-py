from csp_py.interfaces.can_v1 import CspCanV1Interface
from csp_py.packet import CspId, CspPacket, CspPacketPriority


async def test_receive_packets() -> None:
    iface = CspCanV1Interface()

    packets: list[CspPacket] = []

    def packet_sink(packet: CspPacket) -> None:
        packets.append(packet)

    iface.set_packet_sink(packet_sink)

    # Packet 1
    await iface.on_can_frame(0x09300400, bytes.fromhex('8c90200000040000'))
    await iface.on_can_frame(0x09340000, bytes.fromhex('0002'))

    # Packet 2
    await iface.on_can_frame(0x09301405, bytes.fromhex('9268000000290100'))
    await iface.on_can_frame(0x09301405, bytes.fromhex('9268000000290100'))
    await iface.on_can_frame(0x09341005, bytes.fromhex('00ffff46696c6553'))
    await iface.on_can_frame(0x09340C05, bytes.fromhex('797374656d536572'))
    await iface.on_can_frame(0x09340805, bytes.fromhex('766963652e372e34'))
    await iface.on_can_frame(0x09340405, bytes.fromhex('2e302e646576312b'))
    await iface.on_can_frame(0x09340005, bytes.fromhex('67643361643532'))

    assert len(packets) == 2

    assert packets[0].packet_id.src == 6
    assert packets[0].packet_id.dst == 9
    assert packets[0].packet_id.dport == 0
    assert packets[0].packet_id.sport == 32
    assert packets[0].packet_id.priority == CspPacketPriority.Normal
    assert packets[0].data == b'\x00\x00\x00\x02'

    assert packets[1].packet_id.src == 9
    assert packets[1].packet_id.dst == 6
    assert packets[1].packet_id.dport == 32
    assert packets[1].packet_id.sport == 0
    assert packets[1].packet_id.priority == CspPacketPriority.Normal
    assert packets[1].data == b'\x01\x00\x00\xff\xffFileSystemService.7.4.0.dev1+gd3ad52'


async def test_send_packet() -> None:
    iface = CspCanV1Interface()

    frames: list[tuple[int, bytes]] = []

    async def send_frame(frame_id: int, data: bytes) -> None:
        frames.append((frame_id, data))

    iface.send_can_frame = send_frame

    packet = CspPacket(
        packet_id=CspId(src=6, dst=9, dport=0, sport=32, priority=CspPacketPriority.Normal),
        data=b'\x00\x00\x00\x02',
    )

    await iface.send(packet)

    assert len(frames) == 2

    assert frames[0][0] == 0x6480400
    assert frames[0][1] == bytes.fromhex('8c90200000040000')

    assert frames[1][0] == 0x64C0000
    assert frames[1][1] == bytes.fromhex('0002')


async def test_receive_missing_middle_frame() -> None:
    iface = CspCanV1Interface()

    packets: list[CspPacket] = []

    def packet_sink(packet: CspPacket) -> None:
        packets.append(packet)

    iface.set_packet_sink(packet_sink)

    # Packet
    await iface.on_can_frame(0x0AA02000, bytes.fromhex('95478700003c6865'))
    await iface.on_can_frame(0x0AA41C00, bytes.fromhex('6c6c6f206461726b'))
    await iface.on_can_frame(0x0AA41800, bytes.fromhex('6e657373206d7920'))
    await iface.on_can_frame(0x0AA41400, bytes.fromhex('6f6c642066726965'))
    # Missing frame
    # await iface.on_can_frame(0x0AA41000, bytes.fromhex('6e64204976652063'))
    await iface.on_can_frame(0x0AA40C00, bytes.fromhex('6f6d6520746f2074'))
    await iface.on_can_frame(0x0AA40800, bytes.fromhex('616c6b2077697468'))
    await iface.on_can_frame(0x0AA40400, bytes.fromhex('20796f7520616761'))
    await iface.on_can_frame(0x0AA40000, bytes.fromhex('696e'))

    assert len(packets) == 0


async def test_receive_missing_first_frame() -> None:
    iface = CspCanV1Interface()

    packets: list[CspPacket] = []

    def packet_sink(packet: CspPacket) -> None:
        packets.append(packet)

    iface.set_packet_sink(packet_sink)

    # Missing frame
    # await iface.on_can_frame(0x0AA02000, bytes.fromhex('95478700003c6865'))
    await iface.on_can_frame(0x0AA41C00, bytes.fromhex('6c6c6f206461726b'))
    await iface.on_can_frame(0x0AA41800, bytes.fromhex('6e657373206d7920'))
    await iface.on_can_frame(0x0AA41400, bytes.fromhex('6f6c642066726965'))
    await iface.on_can_frame(0x0AA41000, bytes.fromhex('6e64204976652063'))
    await iface.on_can_frame(0x0AA40C00, bytes.fromhex('6f6d6520746f2074'))
    await iface.on_can_frame(0x0AA40800, bytes.fromhex('616c6b2077697468'))
    await iface.on_can_frame(0x0AA40400, bytes.fromhex('20796f7520616761'))
    await iface.on_can_frame(0x0AA40000, bytes.fromhex('696e'))

    assert len(packets) == 0


async def test_restart_packet_when_the_same_cfp_id_received() -> None:
    iface = CspCanV1Interface()
    
    packets: list[CspPacket] = []

    def packet_sink(packet: CspPacket) -> None:
        packets.append(packet)

    iface.set_packet_sink(packet_sink)

    # Packet 1
    await iface.on_can_frame(0x0AA02000, bytes.fromhex('95478700003c6865'))
    await iface.on_can_frame(0x0AA41C00, bytes.fromhex('6c6c6f206461726b'))
    await iface.on_can_frame(0x0AA41800, bytes.fromhex('6e657373206d7920'))
    # unfinished 
    
    # and restarted
    await iface.on_can_frame(0x0AA02000, bytes.fromhex('95478700003c6865'))
    await iface.on_can_frame(0x0AA41C00, bytes.fromhex('6c6c6f206461726b'))
    await iface.on_can_frame(0x0AA41800, bytes.fromhex('6e657373206d7920'))
    await iface.on_can_frame(0x0AA41400, bytes.fromhex('6f6c642066726965'))
    await iface.on_can_frame(0x0AA41000, bytes.fromhex('6e64204976652063'))
    await iface.on_can_frame(0x0AA40C00, bytes.fromhex('6f6d6520746f2074'))
    await iface.on_can_frame(0x0AA40800, bytes.fromhex('616c6b2077697468'))
    await iface.on_can_frame(0x0AA40400, bytes.fromhex('20796f7520616761'))
    await iface.on_can_frame(0x0AA40000, bytes.fromhex('696e'))

    assert len(packets) == 1
    assert packets[0].data == b'hello darkness my old friend Ive come to talk with you again'
