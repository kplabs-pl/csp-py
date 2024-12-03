import pytest
from csp_py import CspRouter

from ..support import CapturingInterface


def test_detect_interface_same_address() -> None:
    router = CspRouter()

    iface1 = CapturingInterface()
    iface2 = CapturingInterface()

    router.add_interface(interface=iface1, address=11, netmask_bits=8)

    with pytest.raises(ValueError):
        router.add_interface(interface=iface2, address=11, netmask_bits=4)


def test_detect_interface_same_network_address() -> None:
    router = CspRouter()

    iface1 = CapturingInterface()
    iface2 = CapturingInterface()

    router.add_interface(interface=iface1, address=0b101010_0000_0000, netmask_bits=6)

    with pytest.raises(ValueError):
        router.add_interface(interface=iface2, address=0b101010_1000_0000, netmask_bits=6)
