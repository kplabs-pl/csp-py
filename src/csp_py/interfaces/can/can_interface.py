from dataclasses import dataclass
import struct
from typing import Any, Awaitable, Callable

from csp_py import CspPacket, CspId, CspPacketPriority, CspPacketFlags
from csp_py.interface import ICspInterface, CspPacketSink


@dataclass
class CfpIdFields:
    begin: bool
    end: bool
    priority: CspPacketPriority
    dst: int
    sender: int
    sc: int
    fc: int

    def as_key(self) -> tuple[int, int, CspPacketPriority, int]:
        return (self.dst, self.sender, self.priority, self.sc)

    def as_num(self) -> int:
        def pack_field(value: int, *, mask: int, offset: int) -> int:
            return (value & mask) << offset
        
        r = 0
        r |= pack_field(self.begin, mask=0x1, offset=1)
        r |= pack_field(self.end, mask=0x1, offset=0)
        r |= pack_field(self.priority.value, mask=0x3, offset=27)
        r |= pack_field(self.dst, mask=0x3FFF, offset=13)
        r |= pack_field(self.sender, mask=0x3F, offset=7)
        r |= pack_field(self.sc, mask=0x3, offset=5)
        r |= pack_field(self.fc, mask=0x7, offset=2)
        return r

@dataclass
class CfpHeaderFields:
    src: int
    dport: int
    sport: int
    flags: CspPacketFlags

    def as_bytes(self) -> bytes:
        def pack_field(value: int, *, mask: int, offset: int) -> int:
            return (value & mask) << offset
        
        r = 0
        r |= pack_field(self.src, mask=0x3FFF, offset=18)
        r |= pack_field(self.dport, mask=0x3F, offset=12)
        r |= pack_field(self.sport, mask=0x3F, offset=6)
        r |= pack_field(self.flags, mask=0x3F, offset=0)
        return struct.pack('!I', r)


def parse_csp_can_frame_id(can_id: int) -> CfpIdFields:
    def extract_field(*, offset: int, mask: int) -> int:
        return (can_id >> offset) & mask

    return CfpIdFields(
            begin=extract_field(mask=0x1, offset=1) == 1,
            end=extract_field(mask=0x1, offset=0) == 1,
            priority=CspPacketPriority(extract_field(mask=0x3, offset=27)),
            dst=extract_field(mask=0x3FFF, offset=13),
            sender=extract_field(mask=0x3F, offset=7),
            sc=extract_field(mask=0x3, offset=5),
            fc=extract_field(mask=0x7, offset=2),
        )

def parse_csp_can_header(data: bytes) -> tuple[CfpHeaderFields, bytes]:
    assert len(data) >= 4
    num, = struct.unpack('!I', data[:4])

    def extract_field(*, offset: int, mask: int) -> int:
        return int((num >> offset) & mask)

    return CfpHeaderFields(
        src=extract_field(mask=0x3FFF, offset=18),
        dport=extract_field(mask=0x3F, offset=12),
        sport=extract_field(mask=0x3F, offset=6),
        flags=CspPacketFlags(extract_field(mask=0x3F, offset=0)),
    ), data[4:]

class CfpReassemblyTracker:
    def __init__(self, id_header: CfpIdFields, header: CfpHeaderFields) -> None:
        self._data = bytearray()
        self._id_header = id_header
        self._header = header

    def append(self, data: bytes) -> None:
        self._data.extend(data)

    def capture(self) -> CspPacket:
        return CspPacket(
            packet_id=CspId(
                priority=self._id_header.priority,
                flags=self._header.flags,
                src=self._header.src,
                dst=self._id_header.dst,
                dport=self._header.dport,
                sport=self._header.sport,
            ),
            data=bytes(self._data),
        )

class CspCanInterface(ICspInterface):
    def __init__(self) -> None:
        self._in_flight: dict[Any, CfpReassemblyTracker] = {}
        self._packet_sink: CspPacketSink | None = None
        self._sender_counter = 0

        self.send_can_frame: Callable[[int, bytes], Awaitable[None]] | None = None

    def set_packet_sink(self, sink: CspPacketSink) -> None:
        self._packet_sink = sink

    async def send(self, packet: CspPacket) -> None:
        data = packet.data

        fragments = []

        fragments.append(data[:4])
        data = data[4:]

        while len(data) > 0:
            fragments.append(data[:8])
            data = data[8:]

        if len(fragments) == 1:
            await self._send_singleton_frame(packet, fragments[0])
        else:
            await self._send_multi_frame(packet, fragments)

    async def _send_singleton_frame(self, packet: CspPacket, fragment: bytes) -> None:
        header = CfpHeaderFields(
            src=packet.packet_id.src,
            dport=packet.packet_id.dport,
            sport=packet.packet_id.sport,
            flags=packet.packet_id.flags,
        )

        can_id = CfpIdFields(begin=True, end=True, priority=packet.packet_id.priority, dst=packet.packet_id.dst, sender=packet.packet_id.src, sc=self._sender_counter, fc=0)

        await self._send_frame(can_id, header.as_bytes() + fragment)

    async def _send_multi_frame(self, packet: CspPacket, fragments: list[bytes]) -> None:
        [begin, *middle, end] = fragments

        header = CfpHeaderFields(
            src=packet.packet_id.src,
            dport=packet.packet_id.dport,
            sport=packet.packet_id.sport,
            flags=packet.packet_id.flags,
        )

        begin = header.as_bytes() + begin

        await self._send_frame(CfpIdFields(begin=True, end=False, priority=packet.packet_id.priority, dst=packet.packet_id.dst, sender=packet.packet_id.src, sc=self._sender_counter, fc=0), begin)

        for idx, f in enumerate(middle):
            await self._send_frame(CfpIdFields(begin=False, end=False, priority=packet.packet_id.priority, dst=packet.packet_id.dst, sender=packet.packet_id.src, sc=self._sender_counter, fc=idx + 1), f)

        await self._send_frame(CfpIdFields(begin=False, end=True, priority=packet.packet_id.priority, dst=packet.packet_id.dst, sender=packet.packet_id.src, sc=self._sender_counter, fc=len(fragments) - 1), end)

    async def _send_frame(self, id_fields: CfpIdFields, data: bytes) -> None:
        can_id = id_fields.as_num()
        assert self.send_can_frame is not None
        await self.send_can_frame(can_id, data)


    async def on_can_frame(self, can_id: int, data: bytes) -> None:
        parsed_id = parse_csp_can_frame_id(can_id)

        key = parsed_id.as_key()

        if parsed_id.begin:
            if len(data) < 4:
                print('[csp.py] Invalid data length')
                return

            header, data = parse_csp_can_header(data)

            self._in_flight[key] = CfpReassemblyTracker(parsed_id, header)

        self._in_flight[key].append(data)

        if parsed_id.end:
            full_packet = self._in_flight.pop(key).capture()
            assert self._packet_sink is not None
            self._packet_sink(full_packet)