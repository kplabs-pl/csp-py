import pytest
from csp_py.rtable import CspRoutingTable

from ..support import CapturingInterface


def test_find_interface_by_entry() -> None:
    table = CspRoutingTable()
    iface = CapturingInterface()
    table.add_entry(network_address=0x100, netmask_bits=6, iface=iface)

    matching_iface = table.iface_for_address(0x102)

    assert id(matching_iface) == id(iface)


def test_find_interface_by_entry_nothing_matches() -> None:
    table = CspRoutingTable()
    iface = CapturingInterface()
    table.add_entry(network_address=0x100, netmask_bits=6, iface=iface)

    matching_iface = table.iface_for_address(0x202)

    assert matching_iface is None


def test_find_interface_with_longest_netmask() -> None:
    table = CspRoutingTable()
    iface1 = CapturingInterface()
    iface2 = CapturingInterface()

    table.add_entry(network_address=0x0100, netmask_bits=6, iface=iface1)
    table.add_entry(network_address=0x0130, netmask_bits=10, iface=iface2)

    assert id(table.iface_for_address(0x144)) == id(iface1)
    assert id(table.iface_for_address(0x138)) == id(iface2)


def test_fail_to_add_duplicate_entry() -> None:
    table = CspRoutingTable()
    iface1 = CapturingInterface()
    iface2 = CapturingInterface()

    table.add_entry(network_address=0x0100, netmask_bits=6, iface=iface1)

    with pytest.raises(ValueError):
        table.add_entry(network_address=0x0100, netmask_bits=6, iface=iface2)
