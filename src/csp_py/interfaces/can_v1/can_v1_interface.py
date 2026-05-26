import asyncio
from dataclasses import dataclass
import math
from typing import Any, Awaitable, Callable

from csp_py import CspPacket, CspId, CspPacketPriority, CspPacketFlags
from csp_py.interface import ICspInterface, CspPacketSink


@dataclass(kw_only=True, frozen=True)
class CfpCanId:
    cfp_id: int
    remaining: int
    frame_type: int
    src: int
    dst: int

    @staticmethod
    def from_can_id(can_id: int) -> 'CfpCanId':
        def extract_bits(*, offset: int, length: int) -> int:
            mask = (1 << length) - 1
            return (can_id >> offset) & mask
        
        return CfpCanId(
            cfp_id=extract_bits(offset=0, length=10),
            remaining=extract_bits(offset=10, length=8),
            frame_type=extract_bits(offset=18, length=1),
            src=extract_bits(offset=19, length=5),
            dst=extract_bits(offset=24, length=5),
        )
    
    def to_can_id(self) -> int:
        return (
            (self.cfp_id & 0x3FF) |
            ((self.remaining & 0xFF) << 10) |
            ((self.frame_type & 0x1) << 18) |
            ((self.src & 0x1F) << 19) |
            ((self.dst & 0x1F) << 24)
        )

    def as_key(self) -> tuple[int, int, int]:
        return (self.src, self.dst, self.cfp_id)

@dataclass(kw_only=True, frozen=True)
class CfpHeader:
    flags: CspPacketFlags
    sport: int
    dport: int
    dst: int
    src: int
    priority: CspPacketPriority

    @staticmethod
    def from_raw(raw: bytes) -> 'CfpHeader':
        if len(raw) != 4:
            raise ValueError(f'CFP header must be 4 bytes, got {len(raw)} bytes')
        
        raw_int = int.from_bytes(raw, byteorder='big')

        def extract_bits(*, offset: int, length: int) -> int:
            mask = (1 << length) - 1
            return (raw_int >> offset) & mask
        
        return CfpHeader(
            flags=CspPacketFlags(extract_bits(offset=0, length=8)),
            sport=extract_bits(offset=8, length=6),
            dport=extract_bits(offset=14, length=6),
            dst=extract_bits(offset=20, length=5),
            src=extract_bits(offset=25, length=5),
            priority=CspPacketPriority(extract_bits(offset=30, length=2)),
        )
    
    def to_raw(self) -> bytes:
        raw_int = (
            (self.flags.value & 0xFF) |
            ((self.sport & 0x3F) << 8) |
            ((self.dport & 0x3F) << 14) |
            ((self.dst & 0x1F) << 20) |
            ((self.src & 0x1F) << 25) |
            ((self.priority.value & 0x3) << 30)
        )
        return raw_int.to_bytes(4, byteorder='big')


class CfpReassemblyTracker:
    def __init__(self, *, cfp_header: CfpHeader, payload_length: int):
        self._cfp_header = cfp_header
        self._payload_length = payload_length
        self._data = bytearray()
        self.completed = False

    def append(self, cfp_id: CfpCanId, data: bytes) -> None:
        # TODO: detect missing/out-of-order packets using cfp_id.remaining
        assert not self.completed, 'cannot append to completed tracker'
        self._data.extend(data)

        if cfp_id.remaining == 0:
            self.completed = True

    def capture(self) -> CspPacket:
        assert self.completed, 'cannot capture incomplete tracker'
        assert len(self._data) == self._payload_length, f'payload length mismatch: expected {self._payload_length}, got {len(self._data)}'
        return CspPacket(
            packet_id=CspId(
                priority=self._cfp_header.priority,
                flags=self._cfp_header.flags,
                src=self._cfp_header.src,
                dst=self._cfp_header.dst,
                dport=self._cfp_header.dport,
                sport=self._cfp_header.sport,
            ),
            data=bytes(self._data),
        )


class CspCanV1Interface(ICspInterface):
    def __init__(self) -> None:
        self.send_can_frame: Callable[[int, bytes], Awaitable[None]] | None = None

        self._in_flight: dict[Any, CfpReassemblyTracker] = {}
        self._send_lock = asyncio.Lock()
        self._packet_counter = 0

    def set_packet_sink(self, sink: CspPacketSink) -> None:
        self._packet_sink = sink

    async def send(self, packet: CspPacket) -> None:
        async with self._send_lock:
            cfp_header = CfpHeader(
                flags=packet.packet_id.flags,
                sport=packet.packet_id.sport,
                dport=packet.packet_id.dport,
                dst=packet.packet_id.dst,
                src=packet.packet_id.src,
                priority=packet.packet_id.priority,
            )
            cfp_header_raw = cfp_header.to_raw()
            data_length_raw = len(packet.data).to_bytes(2, byteorder='big')

            full_packet = cfp_header_raw + data_length_raw + packet.data

            can_frames = math.ceil(len(full_packet) / 8)

            assert self.send_can_frame is not None, 'send_can_frame must be set before sending packets'

            cfp_identifier = self._packet_counter & ((1 << 10) - 1)  # 10 bits for CFP ID
            self._packet_counter += 1

            for i in range(0, can_frames):
                chunk = full_packet[i*8:(i+1)*8]
                cfp_id = CfpCanId(
                    cfp_id=cfp_identifier,
                    remaining=can_frames - i - 1,
                    frame_type=0 if i == 0 else 1,
                    src=cfp_header.src,
                    dst=cfp_header.dst,
                )
                await self.send_can_frame(cfp_id.to_can_id(), chunk)

    async def on_can_frame(self, can_id: int, data: bytes) -> None:
        cfp_id = CfpCanId.from_can_id(can_id)
        is_first_packet = (cfp_id.frame_type == 0)  # 0 = first packet, 1 = continuation packet

        if is_first_packet:
            if len(data) < 6:
                return

            csp_id_raw = data[0:4]
            data_length_raw = data[4:6]
            payload = data[6:]

            x = int.from_bytes(csp_id_raw, byteorder='big')

            data_length = int.from_bytes(data_length_raw, byteorder='big')

            new_tracker = CfpReassemblyTracker(cfp_header=CfpHeader.from_raw(csp_id_raw), payload_length=data_length)
            self._in_flight[cfp_id.as_key()] = new_tracker
            new_tracker.append(cfp_id, payload)
        else:
            existing_tracker = self._in_flight.get(cfp_id.as_key())
            if existing_tracker is None:
                return

            existing_tracker.append(cfp_id, data)

            if existing_tracker.completed:
                full_packet = existing_tracker.capture()
                del self._in_flight[cfp_id.as_key()]
                assert self._packet_sink is not None
                self._packet_sink(full_packet)
