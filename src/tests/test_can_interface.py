from csp_py.interfaces.can import CspCanInterface
from csp_py.packet import CspId, CspPacket, CspPacketPriority


async def test_receive_packets() -> None:
    iface = CspCanInterface()

    packets: list[CspPacket] = []

    def packet_sink(packet: CspPacket) -> None:
        packets.append(packet)

    iface.set_packet_sink(packet_sink)

    # Packet 1
    await iface.on_can_frame(0x10028582, bytes.fromhex('002de1c048656c6c'))
    await iface.on_can_frame(0x10028585, bytes.fromhex('6f20576f726c64'))

    # Packet 2
    await iface.on_can_frame(0x10028502, bytes.fromhex('0029e1c068656c6c'))
    await iface.on_can_frame(0x10028504, bytes.fromhex('6f206461726b6e65'))
    await iface.on_can_frame(0x10028508, bytes.fromhex('7373206d79206f6c'))
    await iface.on_can_frame(0x1002850C, bytes.fromhex('6420667269656e64'))
    await iface.on_can_frame(0x10028510, bytes.fromhex('2049766520636f6d'))
    await iface.on_can_frame(0x10028514, bytes.fromhex('6520746f2074616c'))
    await iface.on_can_frame(0x10028518, bytes.fromhex('6b20776974682079'))
    await iface.on_can_frame(0x1002851D, bytes.fromhex('6f7520616761696e'))

    assert len(packets) == 2

    assert packets[0].packet_id.src == 11
    assert packets[0].packet_id.dst == 20
    assert packets[0].packet_id.dport == 30
    assert packets[0].packet_id.sport == 7
    assert packets[0].packet_id.priority == CspPacketPriority.Normal
    assert packets[0].data == b'Hello World'

    assert packets[1].packet_id.src == 10
    assert packets[1].packet_id.dst == 20
    assert packets[1].packet_id.dport == 30
    assert packets[1].packet_id.sport == 7
    assert packets[1].packet_id.priority == CspPacketPriority.Normal
    assert packets[1].data == b'hello darkness my old friend Ive come to talk with you again'


async def test_send_packet() -> None:
    iface = CspCanInterface()

    frames: list[tuple[int, bytes]] = []

    async def send_frame(frame_id: int, data: bytes) -> None:
        frames.append((frame_id, data))

    iface.send_can_frame = send_frame

    packet = CspPacket(
        packet_id=CspId(src=11, dst=20, dport=30, sport=7, priority=CspPacketPriority.Normal),
        data=b'Hello World',
    )

    await iface.send(packet)

    assert len(frames) == 2

    assert frames[0][0] == 0x10028582
    assert frames[0][1] == bytes.fromhex('002de1c048656c6c')

    assert frames[1][0] == 0x10028585
    assert frames[1][1] == bytes.fromhex('6f20576f726c64')


async def test_receive_missing_middle_frame() -> None:
    iface = CspCanInterface()

    packets: list[CspPacket] = []

    def packet_sink(packet: CspPacket) -> None:
        packets.append(packet)

    iface.set_packet_sink(packet_sink)

    # Packet
    await iface.on_can_frame(0x10028502, bytes.fromhex('0029e1c068656c6c'))
    await iface.on_can_frame(0x10028504, bytes.fromhex('6f206461726b6e65'))
    await iface.on_can_frame(0x10028508, bytes.fromhex('7373206d79206f6c'))
    await iface.on_can_frame(0x1002850C, bytes.fromhex('6420667269656e64'))
    await iface.on_can_frame(0x10028510, bytes.fromhex('2049766520636f6d'))
    await iface.on_can_frame(0x10028514, bytes.fromhex('6520746f2074616c'))
    await iface.on_can_frame(0x10028518, bytes.fromhex('6b20776974682079'))
    # Missing
    # await iface.on_can_frame(0x1002851C, bytes.fromhex('6f7520616761696e'))
    await iface.on_can_frame(0x10028500, bytes.fromhex('2042656361757365'))
    await iface.on_can_frame(0x10028504, bytes.fromhex('206120766973696f'))
    await iface.on_can_frame(0x10028508, bytes.fromhex('6e20736f66746c79'))
    await iface.on_can_frame(0x1002850C, bytes.fromhex('206372656570696e'))
    await iface.on_can_frame(0x10028511, bytes.fromhex('67'))

    assert len(packets) == 0


async def test_receive_missing_first_frame() -> None:
    iface = CspCanInterface()

    packets: list[CspPacket] = []

    def packet_sink(packet: CspPacket) -> None:
        packets.append(packet)

    iface.set_packet_sink(packet_sink)

    # Missing frame
    # await iface.on_can_frame(0x10028502, bytes.fromhex('0029e1c068656c6c'))
    await iface.on_can_frame(0x10028504, bytes.fromhex('6f206461726b6e65'))
    await iface.on_can_frame(0x10028508, bytes.fromhex('7373206d79206f6c'))
    await iface.on_can_frame(0x1002850C, bytes.fromhex('6420667269656e64'))
    await iface.on_can_frame(0x10028510, bytes.fromhex('2049766520636f6d'))
    await iface.on_can_frame(0x10028514, bytes.fromhex('6520746f2074616c'))
    await iface.on_can_frame(0x10028518, bytes.fromhex('6b20776974682079'))
    await iface.on_can_frame(0x1002851C, bytes.fromhex('6f7520616761696e'))
    await iface.on_can_frame(0x10028500, bytes.fromhex('2042656361757365'))
    await iface.on_can_frame(0x10028504, bytes.fromhex('206120766973696f'))
    await iface.on_can_frame(0x10028508, bytes.fromhex('6e20736f66746c79'))
    await iface.on_can_frame(0x1002850C, bytes.fromhex('206372656570696e'))
    await iface.on_can_frame(0x10028511, bytes.fromhex('67'))

    assert len(packets) == 0

async def test_restart_packet_when_the_same_cfp_id_received() -> None:
    iface = CspCanInterface()
    
    packets: list[CspPacket] = []

    def packet_sink(packet: CspPacket) -> None:
        packets.append(packet)

    iface.set_packet_sink(packet_sink)

    # Packet 1
    await iface.on_can_frame(0x10028502, bytes.fromhex('0029e1c068656c6c'))
    await iface.on_can_frame(0x10028504, bytes.fromhex('6f206461726b6e65'))
    await iface.on_can_frame(0x10028508, bytes.fromhex('7373206d79206f6c'))
    # unfinished 
    
    # and restarted
    await iface.on_can_frame(0x10028502, bytes.fromhex('0029e1c068656c6c'))
    await iface.on_can_frame(0x10028504, bytes.fromhex('6f206461726b6e65'))
    await iface.on_can_frame(0x10028508, bytes.fromhex('7373206d79206f6c'))
    await iface.on_can_frame(0x1002850C, bytes.fromhex('6420667269656e64'))
    await iface.on_can_frame(0x10028510, bytes.fromhex('2049766520636f6d'))
    await iface.on_can_frame(0x10028514, bytes.fromhex('6520746f2074616c'))
    await iface.on_can_frame(0x10028518, bytes.fromhex('6b20776974682079'))
    await iface.on_can_frame(0x1002851C, bytes.fromhex('6f7520616761696e'))
    await iface.on_can_frame(0x10028500, bytes.fromhex('2042656361757365'))
    await iface.on_can_frame(0x10028504, bytes.fromhex('206120766973696f'))
    await iface.on_can_frame(0x10028508, bytes.fromhex('6e20736f66746c79'))
    await iface.on_can_frame(0x1002850C, bytes.fromhex('206372656570696e'))
    await iface.on_can_frame(0x10028511, bytes.fromhex('67'))

    assert len(packets) == 1
    assert packets[0].data == (b'hello darkness my old friend Ive come to ' + 
                               b'talk with you again Because a vision softly creeping')
