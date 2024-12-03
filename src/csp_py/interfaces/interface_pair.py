from csp_py.interface import ICspInterface, CspPacketSink
from csp_py.packet import CspPacket


class InterfacePair:
    def __init__(self) -> None:
        self._iface1 = InterfacePair._InterfaceOrPair()
        self._iface2 = InterfacePair._InterfaceOrPair()

        self._iface1.set_other_iface(self._iface2)
        self._iface2.set_other_iface(self._iface1)

    @property
    def iface1(self) -> ICspInterface:
        return self._iface1
    
    @property
    def iface2(self) -> ICspInterface:
        return self._iface2
    

    class _InterfaceOrPair(ICspInterface):
        def __init__(self) -> None:
            self._packet_sink: CspPacketSink | None = None
            self._other_iface: InterfacePair._InterfaceOrPair | None = None

        def set_packet_sink(self, sink: CspPacketSink) -> None:
            self._packet_sink = sink

        def set_other_iface(self, other_iface: 'InterfacePair._InterfaceOrPair') -> None:
            self._other_iface = other_iface

        async def send(self, packet: CspPacket) -> None:
            assert self._other_iface is not None
            self._other_iface.incoming_packet(packet)

        def incoming_packet(self, packet: CspPacket) -> None:
            assert self._packet_sink is not None
            self._packet_sink(packet)
