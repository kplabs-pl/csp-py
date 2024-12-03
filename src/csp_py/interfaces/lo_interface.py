from csp_py.interface import ICspInterface, CspPacketSink
from csp_py.packet import CspPacket


class LoInterface(ICspInterface):
    def __init__(self) -> None:
        super().__init__()
        self._packet_sink: CspPacketSink | None  = None

    def set_packet_sink(self, sink: CspPacketSink) -> None:
        self._packet_sink = sink

    async def send(self, packet: CspPacket) -> None:
        sink = self._packet_sink
        assert sink is not None
        sink(packet)
