from csp_py import CspRouter, CspPacket, CspId, CspPacketPriority, CspPacketFlags
from csp_py.interface import CspPacketSink, ICspInterface


class CapturingInterface(ICspInterface):
    def __init__(self) -> None:
        self.packets: list[CspPacket] = []

    def set_packet_sink(self, sink: CspPacketSink) -> None:
        pass

    async def send(self, packet: CspPacket) -> None:
        self.packets.append(packet)


class CaptureLocalPackets:
    def __init__(self) -> None:
        self.packets: list[CspPacket] = []

    async def __call__(self, packet: CspPacket) -> None:
        self.packets.append(packet)


class CspRouterTest:
    def __init__(self) -> None:
        self.router = CspRouter()
        self.local = CaptureLocalPackets()

        self.router.local_packet_handler = self.local

    def add_interface(self, address: int, netmask_bits: int) -> CapturingInterface:
        iface = CapturingInterface()
        self.router.add_interface(interface=iface, address=address, netmask_bits=netmask_bits)
        return iface

    async def process_incoming(self, *, src: int, dst: int, iface: ICspInterface, data: bytes = b'') -> None:
        packet = CspPacket(
            packet_id=CspId(
                priority=CspPacketPriority.Normal,
                src=src,
                dst=dst,
                sport=10,
                dport=10,
                flags=CspPacketFlags.Zero
            ),
            data=data,
            header=b''
        )
        self.router.push_packet(iface, packet)
        await self.router.process_one_incoming_packet()

    async def send_packet(self, *, src: int, dst: int) -> None:
        packet = CspPacket(
            packet_id=CspId(
                priority=CspPacketPriority.Normal,
                src=src,
                dst=dst,
                sport=10,
                dport=10,
                flags=CspPacketFlags.Zero
            ),
            data=b'',
            header=b''
        )
        await self.router.send_packet(packet)
