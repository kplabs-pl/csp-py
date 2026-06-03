from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, kw_only=True)
class CspAddress:
    address: int
    netbits: int
    version: Literal[1, 2]

    def __post_init__(self) -> None:
        if self.version not in [1, 2]:
            raise ValueError(f"Invalid version: {self.version}")

        if self.version == 2:
            if self.netbits < 0 or self.netbits > 14:
                raise ValueError(f"Invalid netbits: {self.netbits}")

            if self.address < 0 or self.address > 0x3FFF:
                raise ValueError(f"Invalid address: {self.address}")

        if self.version == 1:
            if self.netbits < 0 or self.netbits > 5:
                raise ValueError(f"Invalid netbits: {self.netbits}")

            if self.address < 0 or self.address > 0x1F:
                raise ValueError(f"Invalid address: {self.address}")

    @property
    def address_size(self) -> int:
        match self.version:
            case 1:
                return 5
            case 2:
                return 14
            case _:
                raise ValueError(f"Invalid version: {self.version}")

    @property
    def netmask(self) -> int:
        unshifed_mask = (1 << self.netbits) - 1
        shifted_mask = unshifed_mask << (self.address_size - self.netbits)
        return shifted_mask

    @property
    def node_mask(self) -> int:
        node_bits = self.address_size - self.netbits
        return (1 << node_bits) - 1

    @property
    def network_address(self) -> 'CspAddress':
        network_address = self.address & self.netmask
        return CspAddress(address=network_address, netbits=self.netbits, version=self.version)

    @property
    def broadcast_address(self) -> 'CspAddress':
        return self.with_node_address(self.node_mask)

    def with_node_address(self, node: int) -> 'CspAddress':
        max_node = self.node_mask
        if not (0 <= node <= max_node):
            raise ValueError(f"Invalid node address: {node}. Must be between 0 and {max_node}.")

        return CspAddress(address=self.network_address.address | node, netbits=self.netbits, version=self.version)
