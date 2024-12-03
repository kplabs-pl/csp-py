from .router import CspRouter
from .packet import CspPacket, CspPacketFlags
from .packet_handler import IPacketHandler
from .services.ping import CspPingHandler
from .socket import CspSocketHandler, CspBoundSocket, CspListeningSocket, CspClientConnection
from .interfaces.lo_interface import LoInterface
from .crc32 import register_crc32_filters


class CspNode:
    def __init__(self, *, default_send_flags: CspPacketFlags = CspPacketFlags.Zero) -> None:
        self._default_send_flags = default_send_flags
        self.router = CspRouter()
        self.router.local_packet_handler = self._on_local_packet

        self.router.add_interface(LoInterface(), address=0, netmask_bits=14)

        register_crc32_filters(self.router)

        self._socket_handler = CspSocketHandler()

        self._handlers: list[IPacketHandler] = []

        self.add_packet_handler(CspPingHandler())
        self.add_packet_handler(self._socket_handler)

    def add_packet_handler(self, handler: IPacketHandler) -> None:
        handler.set_send_packet(self._send_packet)
        self._handlers.append(handler)

    def bound_socket(self, port: int | None, *, send_flags: CspPacketFlags=CspPacketFlags.Inherit) -> CspBoundSocket:
        return self._socket_handler.bound_socket(port, send_flags=send_flags)
    
    def listen(self, port: int | None, *, send_flags: CspPacketFlags=CspPacketFlags.Inherit) -> CspListeningSocket:
        return self._socket_handler.listen(port, send_flags=send_flags)
    
    async def connect(self, *, dst: int, port: int, local_port: int | None = None, send_flags: CspPacketFlags=CspPacketFlags.Inherit) -> CspClientConnection:
        return await self._socket_handler.connect(dst, port, local_port, send_flags=send_flags)

    async def _on_local_packet(self, packet: CspPacket) -> None:
        try:
            for handler in self._handlers:
                if await handler.on_packet(packet):
                    return
            
            print('No handler for packet', packet)
        except Exception as e:
            print('Exception in packet handler', e)
            raise e
        
    async def _send_packet(self, packet: CspPacket) -> None:
        resolved_flags = packet.packet_id.flags.resolve(self._default_send_flags)
        packet = packet.with_id(packet.packet_id.with_flags(resolved_flags))
        await self.router.send_packet(packet)
