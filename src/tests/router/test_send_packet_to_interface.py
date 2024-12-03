import pytest
from csp_py import CspPacket

from ..support import CspRouterTest


async def test_no_interface(router: CspRouterTest) -> None:
    with pytest.raises(ValueError):
        await router.send_packet(src=10, dst=20)


async def test_send_to_interface_with_exact_address(router: CspRouterTest) -> None:
    iface = router.add_interface(address=0x723, netmask_bits=6)
    await router.send_packet(src=10, dst=0x723)
    assert len(iface.packets) == 1
    assert iface.packets[0].packet_id.src == 0x723


async def test_send_to_interface_by_matching_network_address(router: CspRouterTest) -> None:
    iface = router.add_interface(address=0x723, netmask_bits=6)
    await router.send_packet(src=10, dst=0x724)
    assert len(iface.packets) == 1
    assert iface.packets[0].packet_id.src == 0x723


async def test_outgoing_packet_filters(router: CspRouterTest) -> None:
    async def packet_filter(packet: CspPacket) -> CspPacket:
        return packet.with_data(b'filtered')
    
    async def packet_filter2(packet: CspPacket) -> CspPacket:
        return packet.with_data(packet.data + b'2')

    router.router.outgoing_packet_filters.append(packet_filter)
    router.router.outgoing_packet_filters.append(packet_filter2)

    iface = router.add_interface(address=0x723, netmask_bits=6)
    await router.send_packet(src=10, dst=0x724)
    assert len(iface.packets) == 1
    assert iface.packets[0].data == b'filtered2'


async def test_send_to_interface_by_routing_table_entry(router: CspRouterTest) -> None:
    iface = router.add_interface(address=0x123, netmask_bits=6)

    router.router.rtable.add_entry(network_address=0x0200, netmask_bits=6, iface=iface)

    await router.send_packet(src=10, dst=0x223)
    assert len(iface.packets) == 1
