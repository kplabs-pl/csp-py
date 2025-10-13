import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, Protocol

from .interface import ICspInterface
from .packet import CspPacket
from .rtable import CspRoutingTable


@dataclass(frozen=True)
class CspInterfaceAddress:
    address: int
    network_address_bits: int

    @property
    def network_mask(self) -> int:
        # TODO: const for address length
        return ((1 << self.network_address_bits) - 1) << (14 - self.network_address_bits)
    
    @property
    def broadcast_address(self) -> int:
        return (~self.network_mask) & 0x3FFF

    @property
    def network_address(self) -> int:
        return self.address & self.network_mask

    def contains_address(self, address: int) -> bool:
        other = CspInterfaceAddress(address=address, network_address_bits=self.network_address_bits)
        return self.network_address == other.network_address


class CspRouterFilter(Protocol):
    async def __call__(self, packet: CspPacket) -> CspPacket | None:
        ...


class CspRouter:
    def __init__(self) -> None:
        self._interfaces: list[tuple[CspInterfaceAddress, ICspInterface]] = []
        self._incoming_packets = asyncio.Queue[tuple[ICspInterface, CspPacket]]()
        self.rtable = CspRoutingTable()
        self.local_packet_handler: Callable[[CspPacket], Awaitable[None]] | None = None

        self.incoming_packet_filters: list[CspRouterFilter] = []
        self.routed_packet_filters: list[CspRouterFilter] = []
        self.outgoing_packet_filters: list[CspRouterFilter] = []

    def push_packet(self, iface: ICspInterface,  packet: CspPacket) -> None:
        self._incoming_packets.put_nowait((iface, packet))

    async def arun(self) -> None:
        try:
            while True:
                await self.process_one_incoming_packet()
        except asyncio.CancelledError:
            pass

    async def process_one_incoming_packet(self) -> None:
        src_iface, packet = await self._incoming_packets.get()

        [src_address] = [addr for addr, iface in self._interfaces if iface == src_iface]

        to_localhost = packet.packet_id.dst in [src_address.address, src_address.broadcast_address]
        if to_localhost:
            await self._process_incoming_packet(packet)
            return
        
        target = self._find_outgoing_interface(packet.packet_id.dst)

        if target is None:
            return
        
        target_address, target_iface = target

        if target_iface == src_iface:
            return

        if target_address.address == packet.packet_id.dst:
            return

        await self._process_routed_packet(packet, target_iface)

    async def _on_packet_to_local(self, packet: CspPacket) -> None:
        assert self.local_packet_handler is not None
        await self.local_packet_handler(packet)

    def add_interface(self, interface: ICspInterface, *, address: int, netmask_bits: int) -> None:
        iface_address = CspInterfaceAddress(address=address, network_address_bits=netmask_bits)

        if any(addr.network_address == iface_address.network_address and addr.network_address_bits != 14 for addr, _ in self._interfaces):
            raise ValueError('An interface with the same network address already exists')

        self._interfaces.append((iface_address, interface))

        
        def sink_packet(packet: CspPacket) -> None:
            self.push_packet(interface, packet)

        interface.set_packet_sink(sink_packet)

    async def send_packet(self, packet: CspPacket) -> None:
        assert isinstance(packet.data, bytes) or isinstance(packet.data, bytearray)

        target = self._find_outgoing_interface(packet.packet_id.dst)
        
        if target is None:
            raise ValueError("no interface matched the packet destination")
        
        iface_addr, iface = target

        packet = packet.with_id(packet.packet_id.with_source(iface_addr.address))
        await self._process_outgoing_packet(packet, iface)

    def _find_outgoing_interface(self, target: int) -> tuple[CspInterfaceAddress, ICspInterface] | None:
        ifaces = [(addr, iface) for addr, iface in self._interfaces if addr.contains_address(target)]

        if len(ifaces) == 1:
            return ifaces[0]
        
        if len(ifaces) > 1:
            raise ValueError('More than one interface matched the packet destination')
        
        iface_by_route = self.rtable.iface_for_address(target)

        if iface_by_route is None:
            return None
    
        [iface_addr] = [addr for (addr, iface) in self._interfaces if iface == iface_by_route]
        return iface_addr, iface_by_route

    async def _process_outgoing_packet(self, packet: CspPacket, iface: ICspInterface) -> None:
        for f in self.outgoing_packet_filters:
            filter_result = await f(packet)
            if filter_result is None:
                return
            packet = filter_result
        await iface.send(packet)

    async def _process_routed_packet(self, packet: CspPacket, to_matching_interface: ICspInterface) -> None:
        await to_matching_interface.send(packet)

    async def _process_incoming_packet(self, packet: CspPacket) -> None:
        for f in self.incoming_packet_filters:
            filter_result = await f(packet)
            if filter_result is None:
                return
            packet = filter_result
            if packet is None:
                return

        await self._on_packet_to_local(packet)
