import pytest


from csp_py import CspAddress


def test_csp_wrong_version() -> None:
    with pytest.raises(ValueError, match="Invalid version: 3"):
        CspAddress(address=0x35BA, netbits=6, version=3)  # type: ignore


def test_csp_v2() -> None:
    assert CspAddress(address=0x35BA, netbits=0, version=2).address_size == 14
    assert CspAddress(address=0x35BA, netbits=0, version=2).netmask == 0
    assert CspAddress(address=0x35BA, netbits=6, version=2).netmask == 0x3F00
    assert CspAddress(address=0x35BA, netbits=6, version=2).node_mask == 0x00FF
    assert CspAddress(address=0x35BA, netbits=6, version=2).network_address == CspAddress(address=0x3500, netbits=6, version=2)
    assert CspAddress(address=0x35BA, netbits=6, version=2).with_node_address(0xAC) == CspAddress(address=0x35AC, netbits=6, version=2)
    assert CspAddress(address=0x35BA, netbits=6, version=2).with_node_address(0xFF) == CspAddress(address=0x35FF, netbits=6, version=2)
    assert CspAddress(address=0x35BA, netbits=6, version=2).broadcast_address == CspAddress(address=0x35FF, netbits=6, version=2)
    assert CspAddress(address=0x35BA, netbits=6, version=2).contains(0x3520)
    assert not CspAddress(address=0x35BA, netbits=6, version=2).contains(0x3620)


def test_csp_v2_wrong_netbits() -> None:
    with pytest.raises(ValueError, match="Invalid netbits: 15"):
        CspAddress(address=0x35BA, netbits=15, version=2)

    with pytest.raises(ValueError, match="Invalid netbits: -2"):
        CspAddress(address=0x35BA, netbits=-2, version=2)


def test_csp_v2_wrong_address() -> None:
    with pytest.raises(ValueError, match="Invalid address: -20"):
        CspAddress(address=-20, netbits=3, version=2)

    with pytest.raises(ValueError, match="Invalid address: 16384"):
        CspAddress(address=0x4000, netbits=3, version=2)


def test_csp_v2_wrong_with_node_address() -> None:
    with pytest.raises(ValueError, match="Invalid node address: 428"):
        assert CspAddress(address=0x35BA, netbits=6, version=2).with_node_address(0x1AC)

    with pytest.raises(ValueError, match="Invalid node address: -20"):
        assert CspAddress(address=0x35BA, netbits=6, version=2).with_node_address(-20)


def test_csp_v2_list_addresses_in_network() -> None:
    address = CspAddress(address=0x35BA, netbits=10, version=2)
    all_addresses_in_network = address.list_addresses_in_network()
    assert len(all_addresses_in_network) == 16

    for i in range(16):
        assert CspAddress(address=0x35B0 + i, netbits=10, version=2) in all_addresses_in_network


def test_csp_v1() -> None:
    assert CspAddress(address=0b11011, netbits=0, version=1).address_size == 5
    assert CspAddress(address=0b11011, netbits=0, version=1).netmask == 0
    assert CspAddress(address=0b11011, netbits=3, version=1).netmask == 0b11100
    assert CspAddress(address=0b11011, netbits=3, version=1).node_mask == 0b00011
    assert CspAddress(address=0b11011, netbits=3, version=1).network_address == CspAddress(address=0b11000, netbits=3, version=1)
    assert CspAddress(address=0b11011, netbits=2, version=1).with_node_address(0b101) == CspAddress(address=0b11101, netbits=2, version=1)
    assert CspAddress(address=0b11011, netbits=2, version=1).with_node_address(0b111) == CspAddress(address=0b11111, netbits=2, version=1)
    assert CspAddress(address=0b11011, netbits=2, version=1).broadcast_address == CspAddress(address=0b11111, netbits=2, version=1)
    assert CspAddress(address=0b11011, netbits=2, version=1).contains(0b11101)
    assert not CspAddress(address=0b11011, netbits=2, version=1).contains(0b01101)


def test_csp_v1_wrong_netbits() -> None:
    with pytest.raises(ValueError, match="Invalid netbits: 6"):
        CspAddress(address=0b11011, netbits=6, version=1)

    with pytest.raises(ValueError, match="Invalid netbits: -2"):
        CspAddress(address=0b11011, netbits=-2, version=1)


def test_csp_v1_wrong_address() -> None:
    with pytest.raises(ValueError, match="Invalid address: -20"):
        CspAddress(address=-20, netbits=3, version=1)

    with pytest.raises(ValueError, match="Invalid address: 32"):
        CspAddress(address=0x20, netbits=3, version=1)


def test_csp_v1_wrong_with_node_address() -> None:
    with pytest.raises(ValueError, match="Invalid node address: 9"):
        assert CspAddress(address=0b11011, netbits=2, version=1).with_node_address(0b1001)

    with pytest.raises(ValueError, match="Invalid node address: -20"):
        assert CspAddress(address=0b11011, netbits=2, version=1).with_node_address(-20)


def test_csp_v1_list_addresses_in_network() -> None:
    address = CspAddress(address=0b11011, netbits=2, version=1)
    all_addresses_in_network = address.list_addresses_in_network()
    assert len(all_addresses_in_network) == 8

    for i in range(8):
        assert CspAddress(address=0b11000 + i, netbits=2, version=1) in all_addresses_in_network
