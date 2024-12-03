from dataclasses import dataclass

from .interface import ICspInterface


@dataclass(frozen=True)
class Route:
    network_address: int
    netmask_bits: int
    iface: ICspInterface

    def __post_init__(self) -> None:
        assert (self.network_address & ~self.netmask) == 0, 'Network address must have node address set to 0'

    @property
    def netmask(self) -> int:
        return ((1 << self.netmask_bits) - 1) << (14 - self.netmask_bits)

    def routes_to_address(self, target: int) -> bool:
        target_network = target & self.netmask
        return target_network == self.network_address


class CspRoutingTable:
    def __init__(self) -> None:
        self._routes: list[Route] = []

    def add_entry(self, *, network_address: int, netmask_bits: int, iface: ICspInterface) -> None:
        if any(route for route in self._routes if route.network_address == network_address and route.netmask_bits == netmask_bits):
            raise ValueError('Duplicate route entry')
        # TODO: check for duplicate entry
        self._routes.append(Route(
            network_address=network_address,
            netmask_bits=netmask_bits, 
            iface=iface
        ))

    def iface_for_address(self, address: int) -> ICspInterface | None:
        matching_routes = [route for route in self._routes if route.routes_to_address(address)]
        
        if len(matching_routes) == 0:
            return None
        
        if len(matching_routes) == 1:
            return matching_routes[0].iface

        matching_routes = list(sorted(matching_routes, key=lambda r: r.netmask_bits, reverse=True))

        return matching_routes[0].iface
