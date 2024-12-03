from abc import ABC, abstractmethod
from typing import Protocol

from .packet import CspPacket


class CspPacketSink(Protocol):
    def __call__(self, packet: CspPacket) -> None:
        raise NotImplementedError()


class ICspInterface(ABC):
    @abstractmethod
    def set_packet_sink(self, sink: CspPacketSink) -> None:
        pass

    @abstractmethod
    async def send(self, packet: CspPacket) -> None:
        raise NotImplementedError()
