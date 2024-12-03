from ..support import CspRouterTest


async def test_incoming_packet_to_matching_interface(router: CspRouterTest) -> None:
    iface1 = router.add_interface(address=0x789, netmask_bits=6)
    iface2 = router.add_interface(address=0x589, netmask_bits=6)
    await router.process_incoming(iface=iface2, src=10, dst=0x788)

    assert len(iface1.packets) == 1
    assert len(iface2.packets) == 0


async def test_incoming_packet_to_interface_by_rtable(router: CspRouterTest) -> None:
    iface1 = router.add_interface(address=0x0600, netmask_bits=6)
    iface2 = router.add_interface(address=0x0800, netmask_bits=6)
    router.router.rtable.add_entry(network_address=0x700, netmask_bits=6, iface=iface1)

    await router.process_incoming(iface=iface2, src=10, dst=0x701)

    assert len(iface1.packets) == 1


async def test_dont_route_packet_to_interface_it_came_from(router: CspRouterTest) -> None:
    incoming_iface = router.add_interface(address=0x0600, netmask_bits=6)

    await router.process_incoming(iface=incoming_iface, src=0x0620, dst=0x0610)

    assert len(incoming_iface.packets) == 0
    assert len(router.local.packets) == 0
