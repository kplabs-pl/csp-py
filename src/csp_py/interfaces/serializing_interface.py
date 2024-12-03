from dataclasses import dataclass
import struct
from typing import Protocol

from ..interface import ICspInterface, CspPacketSink
from csp_py import CspPacket, CspId, CspPacketPriority, CspPacketFlags


@dataclass(frozen=True)
class FieldInfo:
    mask: int
    offset: int

    def extract(self, value: int) -> int:
        return (value >> self.offset) & self.mask
    
    def pack(self, value: int) -> int:
        return (value & self.mask) << self.offset


class CspIdLayout:
    Priority = FieldInfo(3, 46)
    Destination = FieldInfo(0x3FFF, 32)
    Source = FieldInfo(0x3FFF, 18)
    DestinationPort = FieldInfo(0x3F, 12)
    SourcePort = FieldInfo(0x3F, 6)
    Flags = FieldInfo(0x3F, 0)

    @staticmethod
    def from_int(value: int) -> CspId:
        return CspId(
            priority=CspPacketPriority(CspIdLayout.Priority.extract(value)),
            dst=CspIdLayout.Destination.extract(value),
            src=CspIdLayout.Source.extract(value),
            dport=CspIdLayout.DestinationPort.extract(value),
            sport=CspIdLayout.SourcePort.extract(value),
            flags=CspPacketFlags(CspIdLayout.Flags.extract(value)),
        )
    
    @staticmethod
    def to_int(id: CspId) -> int:
        return (
            CspIdLayout.Priority.pack(id.priority.value) |
            CspIdLayout.Destination.pack(id.dst) |
            CspIdLayout.Source.pack(id.src) |
            CspIdLayout.DestinationPort.pack(id.dport) |
            CspIdLayout.SourcePort.pack(id.sport) |
            CspIdLayout.Flags.pack(id.flags.value)
        )

class SerializedFrameSink(Protocol):
    async def __call__(self, frame: bytes) -> None:
        ...


class CspSerializingInterface(ICspInterface):
    def __init__(self, on_frame: SerializedFrameSink) -> None:
        self._frame_sink = on_frame
        self._packet_sink: CspPacketSink | None = None

    def set_packet_sink(self, sink: CspPacketSink) -> None:
        self._packet_sink = sink

    async def send(self, packet: CspPacket) -> None:
        header_num = CspIdLayout.to_int(packet.packet_id)
        header = struct.pack('!Q', header_num)[2:]
        frame = header + packet.data
        await self._frame_sink(frame)

    async def on_incoming_frame(self, frame: bytes) -> None:
        header = b'\x00\x00' + frame[:6]
        payload = frame[6:]
        header_num, =  struct.unpack('!Q', header)
        incoming_id = CspIdLayout.from_int(header_num)
        packet = CspPacket(
            packet_id=incoming_id,
            data=payload,
        )
        sink = self._packet_sink
        assert sink is not None
        sink(packet)
