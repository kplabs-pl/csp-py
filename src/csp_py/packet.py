from dataclasses import dataclass
from enum import Enum, IntFlag


class CspPacketPriority(Enum):
    Critical = 0
    High = 1
    Normal = 2
    Low = 3


class CspPacketFlags(IntFlag):
    Zero = 0
    CRC32 = 1

    Inherit = 0xFF00_0000

    def resolve(self, inherit: 'CspPacketFlags') -> 'CspPacketFlags':
        if CspPacketFlags.Inherit in self:
            v = self - CspPacketFlags.Inherit
            v |= inherit
            return CspPacketFlags(v).resolve(CspPacketFlags.Zero)
        else:
            return CspPacketFlags(self)


@dataclass(frozen=True)
class CspId:
    src: int
    dst: int
    dport: int
    sport: int
    flags: CspPacketFlags = CspPacketFlags.Zero
    priority: CspPacketPriority = CspPacketPriority.Normal

    def reply_id(self) -> 'CspId':
        return CspId(
            priority=self.priority,
            flags=self.flags,
            src=self.dst,
            dst=self.src,
            dport=self.sport,
            sport=self.dport,
        )

    def with_source(self, src: int) -> 'CspId':
        return CspId(
            priority=self.priority,
            flags=self.flags,
            src=src,
            dst=self.dst,
            dport=self.dport,
            sport=self.sport,
        )
    
    def with_flags(self, flags: CspPacketFlags) -> 'CspId':
        return CspId(
            priority=self.priority,
            flags=flags,
            src=self.src,
            dst=self.dst,
            dport=self.dport,
            sport=self.sport,
        )


@dataclass(frozen=True)
class CspPacket:
    packet_id: CspId
    header: bytes = b''
    data: bytes = b''

    def with_id(self, new_id: CspId) -> 'CspPacket':
        return CspPacket(
            packet_id=new_id,
            header=self.header,
            data=self.data,
        )

    def with_data(self, new_data: bytes) -> 'CspPacket':
        return CspPacket(
            packet_id=self.packet_id,
            header=self.header,
            data=new_data,
        )
