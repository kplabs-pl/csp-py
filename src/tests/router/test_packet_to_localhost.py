from csp_py import CspPacket

from ..support import CspRouterTest


# async def test_no_interfaces(router: CspRouterTest) -> None:
#     await router.process_incoming(src=10, dst=11)

#     assert len(router.local.packets) == 0


async def test_single_interface_matching(router: CspRouterTest) -> None:
    iface = router.add_interface(address=11, netmask_bits=8)

    await router.process_incoming(iface=iface, src=10, dst=11)

    assert len(iface.packets) == 0
    assert len(router.local.packets) == 1


async def test_single_interface_not_matching(router: CspRouterTest) -> None:
    iface = router.add_interface(address=11, netmask_bits=8)

    await router.process_incoming(iface=iface, src=10, dst=0x1112)

    assert len(iface.packets) == 0
    assert len(router.local.packets) == 0


async def test_multiple_interface_single_matching(router: CspRouterTest) -> None:
    iface1 = router.add_interface(address=0x111, netmask_bits=8)
    iface2 = router.add_interface(address=0x212, netmask_bits=8)

    await router.process_incoming(iface=iface2, src=10, dst=0x212)

    assert len(iface1.packets) == 0
    assert len(iface2.packets) == 0
    assert len(router.local.packets) == 1


async def test_multiple_interface_no_matching(router: CspRouterTest) -> None:
    iface1 = router.add_interface(address=0x111, netmask_bits=8)
    iface2 = router.add_interface(address=0x212, netmask_bits=8)

    await router.process_incoming(iface=iface2, src=10, dst=0x1413)

    assert len(iface1.packets) == 0
    assert len(iface2.packets) == 0
    assert len(router.local.packets) == 0


async def test_single_interface_broadcast_address(router: CspRouterTest) -> None:
    iface = router.add_interface(address=0x111, netmask_bits=6)

    await router.process_incoming(iface=iface, src=10, dst=0xFF)  # TODO: wrong addresses?

    assert len(iface.packets) == 0
    assert len(router.local.packets) == 1


async def test_incoming_packet_filters(router: CspRouterTest) -> None:
    async def packet_filter(packet: CspPacket) -> CspPacket:
        return packet.with_data(b'filtered')
    
    async def packet_filter2(packet: CspPacket) -> CspPacket:
        return packet.with_data(packet.data + b'2')

    router.router.incoming_packet_filters.append(packet_filter)
    router.router.incoming_packet_filters.append(packet_filter2)

    iface = router.add_interface(address=0x111, netmask_bits=8)

    await router.process_incoming(iface=iface, src=10, dst=0x111)

    assert len(iface.packets) == 0
    assert len(router.local.packets) == 1
    assert router.local.packets[0].data == b'filtered2'


async def test_drop_packet_with_localhost_address_but_of_different_interface(router: CspRouterTest) -> None:
    iface1 = router.add_interface(address=0x0102, netmask_bits=6)
    iface2 = router.add_interface(address=0x0202, netmask_bits=6)

    await router.process_incoming(iface=iface2, src=10, dst=0x0102)

    assert len(iface1.packets) == 0
    assert len(iface2.packets) == 0
    assert len(router.local.packets) == 0