from csp_py.address import CspAddress

from ..support import CspRouterTest


async def test_route_to_interface_considering_csp_version(router: CspRouterTest) -> None:
    iface1 = router.add_interface(address=CspAddress(address=0b00_0000_0000_0001, netbits=10, version=2))  # CSPv2 address (network addresss = 0b00_0000_0000_0000)
    iface2 = router.add_interface(address=CspAddress(address=0b10001, netbits=3, version=1))  # CSPv1 address (network address = 0b10000)
    iface3 = router.add_interface(address=CspAddress(address=0b11001, netbits=3, version=1))  # CSPv1 address (network address = 0b11000)

    await router.send_packet(src=10, dst=0b11001, payload=b'iface3')
    await router.send_packet(src=11, dst=0b10001, payload=b'iface2')
    await router.send_packet(src=0, dst=0b00_0000_0000_0011, payload=b'iface1')

    assert len(iface1.packets) == 1
    assert len(iface2.packets) == 1
    assert len(iface3.packets) == 1


    assert iface1.packets[0].data == b'iface1'
    assert iface2.packets[0].data == b'iface2'
    assert iface3.packets[0].data == b'iface3'
