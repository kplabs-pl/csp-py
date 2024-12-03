import asyncio
import time
from csp_py import CspNode, ping
from csp_py.packet import CspId, CspPacket, CspPacketPriority, CspPacketFlags
from csp_py.services.ping import CspPingHandler


async def test_ping() -> None:
    handler = CspPingHandler()

    packets: list[CspPacket] = []
    async def capture_packet(packet: CspPacket) -> None:
        packets.append(packet)

    handler.set_send_packet(capture_packet)

    r = await handler.on_packet(CspPacket(
        packet_id=CspId(
            priority=CspPacketPriority.High,
            flags=CspPacketFlags(12),
            src=10,
            dst=20,
            dport=1,
            sport=40
        ),
        header=b'abcd',
        data=b'hello world'
    ))

    assert r == True
    assert len(packets) == 1
    assert packets[0].packet_id.priority == CspPacketPriority.High
    assert packets[0].packet_id.flags == 12
    assert packets[0].packet_id.src == 20
    assert packets[0].packet_id.dst == 10
    assert packets[0].packet_id.sport == 1
    assert packets[0].packet_id.dport == 40
    assert packets[0].header == b'abcd'
    assert packets[0].data == b'hello world'


async def test_ignore_other_packets() -> None:
    handler = CspPingHandler()

    r = await handler.on_packet(CspPacket(
        packet_id=CspId(
            priority=CspPacketPriority.High,
            flags=CspPacketFlags(12),
            src=10,
            dst=20,
            dport=2,
            sport=40
        ),
        header=b'abcd',
        data=b'hello world'
    ))

    assert r == False


async def test_send_ping(node: CspNode) -> None:
    async def delay_packet(packet: CspPacket) -> CspPacket:
        await asyncio.sleep(0.5)
        return packet

    node.router.incoming_packet_filters.append(delay_packet)
    roundtrip = await ping(node, dst=0)

    assert 1.5 > roundtrip > 0.5
