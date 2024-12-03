from abc import ABC, abstractmethod
from typing import Protocol

from .packet import CspPacket


class IPacketHandler(ABC):
    class SendPacket(Protocol):
        async def __call__(self, packet: CspPacket) -> None:
            raise NotImplementedError()

    def __init__(self) -> None:
        self._send_packet: IPacketHandler.SendPacket | None = None

    def set_send_packet(self, send_packet: SendPacket) -> None:
        self._send_packet = send_packet

    async def send_packet(self, packet: CspPacket) -> None:
        assert self._send_packet is not None
        await self._send_packet(packet)

    @abstractmethod
    async def on_packet(self, packet: CspPacket) -> bool:
        raise NotImplementedError()
