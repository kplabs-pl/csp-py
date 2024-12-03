from ..packet_handler import IPacketHandler
from ..packet import CspPacket, CspPacketFlags


class CspPingHandler(IPacketHandler):
    async def on_packet(self, packet: CspPacket) -> bool:
        if packet.packet_id.dport == 1:
            response = CspPacket(
                packet_id=packet.packet_id.reply_id(),
                header=packet.header,
                data=packet.data,
            )
            await self.send_packet(response)
            return True
        else:
            return False

