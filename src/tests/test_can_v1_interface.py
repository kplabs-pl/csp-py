from csp_py.interfaces.can_v1 import CspCanV1Interface
from csp_py.packet import CspPacket, CspPacketPriority

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
