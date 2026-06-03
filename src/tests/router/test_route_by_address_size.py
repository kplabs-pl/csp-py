from csp_py import CspPacket

from ..support import CspRouterTest


async def test_single_interface_matching(router: CspRouterTest) -> None:
    iface1 = router.add_interface(address=0b00_0000_0000_0001, netmask_bits=10)  # CSPv2 address (network addresss = 0b00_0000_0000_0000)
    iface2 = router.add_interface(address=0b10001, netmask_bits=3)  # CSPv1 address (network address = 0b10000)
    iface3 = router.add_interface(address=0b11001, netmask_bits=3)  # CSPv1 address (network address = 0b11000)

    await router.send_packet(src=10, dst=0b11001)

    assert len(iface1.packets) == 0
    assert len(iface2.packets) == 0
    assert len(iface3.packets) == 1
