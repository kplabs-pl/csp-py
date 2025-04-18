from csp_py import CspPacket, CspId, CspPacketPriority, CspPacketFlags
from csp_py.crc32 import  register_crc32_filters

from .support import CspRouterTest


async def test_append_crc32_to_outgoing_packets_if_enabled(router: CspRouterTest) -> None:
    register_crc32_filters(router.router)

    packet = CspPacket(
        packet_id=CspId(
            priority=CspPacketPriority.Normal,
            flags=CspPacketFlags.CRC32,
            src=0,
            dst=2,
            sport=10,
            dport=10
        ),
        data=b'hello world'
    )
    iface = router.add_interface(2, 2)
    await router.router.send_packet(packet)
    
    assert len(iface.packets) == 1
    assert iface.packets[0].data == b'hello world\xc9\x94e\xaa'


async def test_dont_append_crc32_to_outgoing_packets_if_enabled(router: CspRouterTest) -> None:
    register_crc32_filters(router.router)

    packet = CspPacket(
        packet_id=CspId(
            priority=CspPacketPriority.Normal,
            flags=CspPacketFlags.Zero,
            src=0,
            dst=2,
            sport=10,
            dport=10
        ),
        data=b'hello world'
    )
    iface = router.add_interface(2, 2)
    await router.router.send_packet(packet)
    
    assert len(iface.packets) == 1
    assert iface.packets[0].data == b'hello world'


async def test_drop_crc32_from_incoming_packets_if_enabled(router: CspRouterTest) -> None:
    register_crc32_filters(router.router)

    iface = router.add_interface(2, 2)

    packet = CspPacket(
            packet_id=CspId(
                priority=CspPacketPriority.Normal,
                src=3,
                dst=2,
                sport=10,
                dport=10,
                flags=CspPacketFlags.CRC32
            ),
            data=b'hello world\xc9\x94e\xaa',
            header=b''
        )
    router.router.push_packet(iface, packet)
    await router.router.process_one_incoming_packet()

    assert len(router.local.packets) == 1
    assert router.local.packets[0].data == b'hello world'


async def test_dont_drop_crc32_from_incoming_packets_if_enabled(router: CspRouterTest) -> None:
    register_crc32_filters(router.router)

    iface = router.add_interface(2, 2)

    packet = CspPacket(
            packet_id=CspId(
                priority=CspPacketPriority.Normal,
                src=3,
                dst=2,
                sport=10,
                dport=10,
                flags=CspPacketFlags.Zero
            ),
            data=b'hello world\xc9\x94e\xaa',
            header=b''
        )
    router.router.push_packet(iface, packet)
    await router.router.process_one_incoming_packet()

    assert len(router.local.packets) == 1
    assert router.local.packets[0].data == b'hello world\xc9\x94e\xaa'


async def test_drop_incoming_packet_if_crc32_invalid(router: CspRouterTest) -> None:
    register_crc32_filters(router.router)

    iface = router.add_interface(2, 2)

    packet = CspPacket(
            packet_id=CspId(
                priority=CspPacketPriority.Normal,
                src=3,
                dst=2,
                sport=10,
                dport=10,
                flags=CspPacketFlags.CRC32
            ),
            data=b'hello world\xc9\x94e\xbb',
            header=b''
        )
    router.router.push_packet(iface, packet)
    await router.router.process_one_incoming_packet()

    assert len(router.local.packets) == 0


async def test_drop_incoming_packet_if_too_short_for_crc32(router: CspRouterTest) -> None:
    register_crc32_filters(router.router)

    iface = router.add_interface(2, 2)

    packet = CspPacket(
            packet_id=CspId(
                priority=CspPacketPriority.Normal,
                src=3,
                dst=2,
                sport=10,
                dport=10,
                flags=CspPacketFlags.CRC32
            ),
            data=b'abc',
            header=b''
        )
    router.router.push_packet(iface, packet)
    await router.router.process_one_incoming_packet()

    assert len(router.local.packets) == 0


async def test_dont_drop_incoming_packet_with_only_crc32(router: CspRouterTest) -> None:
    register_crc32_filters(router.router)

    iface = router.add_interface(2, 2)

    packet = CspPacket(
            packet_id=CspId(
                priority=CspPacketPriority.Normal,
                src=3,
                dst=2,
                sport=10,
                dport=10,
                flags=CspPacketFlags.CRC32
            ),
            data=b'\x00\x00\x00\x00',
            header=b''
        )
    router.router.push_packet(iface, packet)
    await router.router.process_one_incoming_packet()

    assert len(router.local.packets) == 1
    assert router.local.packets[0].data == b''