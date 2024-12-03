from abc import ABC, abstractmethod
import asyncio
from csp_py.packet_handler import IPacketHandler
from .packet import CspPacket, CspId, CspPacketPriority, CspPacketFlags


# TODO: separate impl

class BindAnyPort:
    pass


Port = int | BindAnyPort

class CspPortHandler(ABC):
    @abstractmethod
    async def _add_incoming_packet(self, packet: CspPacket) -> None:
        pass

class CspServerConnection:
    def __init__(self, owner: 'CspListeningSocket', dst: int, port: int, local_port: int) -> None:
        self._owner = owner
        self._dst: int | None = dst
        self._port: int | None = port
        self._local_port: int | None = local_port
        self._pending_packets = asyncio.Queue[CspPacket]()

    @property
    def remote_address(self) -> int:
        assert self._dst is not None
        return self._dst

    @property
    def remote_port(self) -> int:
        assert self._port is not None
        return self._port

    @property
    def local_port(self) -> int:
        assert self._local_port is not None
        return self._local_port

    def __del__(self) -> None:
        self.close()
    
    def close(self) -> None:
        if self._dst is not None and self._port is not None:
            self._owner._delete_connection(self._dst, self._port)
            self._dst = None
            self._port = None

    async def send(self, data: bytes) -> None:
        assert self._dst is not None 
        assert self._port is not None
        assert self._local_port is not None
        await self._owner._send_to(dst=self._dst, port=self._port, local_port=self._local_port, data=data)

    async def recv(self) -> CspPacket:
        return await self._pending_packets.get()
    
    async def _add_incoming_packet(self, packet: CspPacket) -> None:
        await self._pending_packets.put(packet)


class CspBoundSocket(CspPortHandler):
    def __init__(self, handler: 'CspSocketHandler', port: Port, send_flags: CspPacketFlags) -> None:
        self._handler = handler
        self._port: Port | None = None
        self._pending_packets = asyncio.Queue[CspPacket]()
        self._handler.bind(port, self)
        self._port = port
        self._send_flags = send_flags

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        if self._port is not None:
            self._handler.unbind(self._port)

        self._port = None

    async def send_to(self, *, dst: int, port: int, data: bytes) -> None:
        assert self._port is not None
        assert not isinstance(self._port, BindAnyPort)
        packet = CspPacket(
            packet_id=CspId(
                priority=CspPacketPriority.Normal, # TODO
                flags=self._send_flags,
                src=0,
                sport=self._port,
                dst=dst,
                dport=port,
            ),
            data=data,
        )
        await self._handler.send_packet(packet)

    async def _add_incoming_packet(self, packet: CspPacket) -> None:
        await self._pending_packets.put(packet)

    async def send_reply(self, request: CspPacket, response: bytes) -> None:
        assert self._port is not None

        if not isinstance(self._port, BindAnyPort) and request.packet_id.dport != self._port:
            raise ValueError(f'Invalid destination port in request (port in request {request.packet_id.dport} but bound to {self._port})')

        packet = CspPacket(
            packet_id=CspId(
                priority=CspPacketPriority.Normal, # TODO
                flags=self._send_flags,
                src=0,
                sport=request.packet_id.dport,
                dst=request.packet_id.src,
                dport=request.packet_id.sport,
            ),
            data=response,
        )
        await self._handler.send_packet(packet)
    
    async def recv_from(self) -> CspPacket:
        return await self._pending_packets.get()


class CspListeningSocket(CspPortHandler):
    ConnectionId = tuple[int, int]

    def __init__(self, owner: 'CspSocketHandler', local_port: Port, send_flags: CspPacketFlags) -> None:
        self._owner = owner
        self._local_port: Port | None = None
        owner.bind(local_port, self)
        self._local_port = local_port
        self._send_flags = send_flags
        self._connections: dict[CspListeningSocket.ConnectionId, CspServerConnection] = {}
        self._pending_packets = asyncio.Queue[CspPacket]()
        self._pending_connections = asyncio.Queue[CspListeningSocket.ConnectionId]()

    def __del__(self) -> None:
        self.close()

    async def accept(self) -> CspServerConnection:
        conn_id = await self._pending_connections.get()
        return self._connections[conn_id]
    
    def close(self) -> None:
        if self._local_port is not None:
            self._owner.unbind(self._local_port)
            self._local_port = None
    
    async def _add_incoming_packet(self, packet: CspPacket) -> None:
        connection_id = self._conn_id(packet)
        connection = self._connections.get(connection_id, None)
        if connection is not None:
            await connection._add_incoming_packet(packet)
        else:
            connection = CspServerConnection(self, packet.packet_id.src, packet.packet_id.sport, packet.packet_id.dport)
            self._connections[connection_id] = connection
            await connection._add_incoming_packet(packet)
            await self._pending_connections.put(connection_id)

    def _delete_connection(self, address: int, port: int) -> None:
        del self._connections[(address, port)]

    async def _send_to(self, *, dst: int, port: int, local_port: int, data: bytes) -> None:
        assert self._local_port is not None

        packet = CspPacket(
            packet_id=CspId(
                dst=dst,
                dport=port,
                src=0,
                sport=local_port,
                flags=self._send_flags,
                priority=CspPacketPriority.Normal
            ),
            header=b'',
            data=data
        )
        await self._owner.send_packet(packet)

    @staticmethod
    def _conn_id(packet: CspPacket) -> ConnectionId:
        return (packet.packet_id.src, packet.packet_id.sport)


class CspClientConnection:
    def __init__(self, socket: CspBoundSocket, remote_address: int, remote_port: int) -> None:
        super().__init__()
        self._socket = socket
        self._remote_address = remote_address
        self._remote_port = remote_port

    async def send(self, data: bytes) -> None:
        await self._socket.send_to(dst=self._remote_address, port=self._remote_port, data=data)
    
    async def recv(self) -> CspPacket:
        while True:
            packet = await self._socket.recv_from()

            if packet.packet_id.src == self._remote_address and packet.packet_id.sport == self._remote_port:
                return packet
    
    def close(self) -> None:
        self._socket.close()

    @staticmethod
    async def _connect(local_socket: CspBoundSocket, dst: int, port: int, local_port: int) -> 'CspClientConnection':
        return CspClientConnection(local_socket, dst, port)


class CspSocketHandler(IPacketHandler):
    ANY_PORT = 0xFFFF_FFFF

    def __init__(self) -> None:
        super().__init__()
        self._ports: dict[int, CspPortHandler] = {}

    def bound_socket(self, port: int | None, *, send_flags: CspPacketFlags) -> CspBoundSocket:
        bind_to: Port | None = port 
        if bind_to is None:
            bind_to = BindAnyPort()
        socket = CspBoundSocket(self, bind_to, send_flags=send_flags)
        return socket

    def listen(self, port: int | None, *, send_flags: CspPacketFlags) -> CspListeningSocket:
        bind_to: Port | None = port 
        if bind_to is None:
            bind_to = BindAnyPort()
        socket = CspListeningSocket(self, bind_to, send_flags=send_flags)
        return socket
    
    async def connect(self, remote_address: int, remote_port: int, local_port: int | None, *, send_flags: CspPacketFlags) -> CspClientConnection:
        if local_port is None:
            local_port = self._find_free_port()
        local_socket = self.bound_socket(local_port, send_flags=send_flags)
        connection = await CspClientConnection._connect(local_socket, remote_address, remote_port, local_port)
        return connection

    async def on_packet(self, packet: CspPacket) -> bool:
        handler = self._ports.get(packet.packet_id.dport)
        if handler is None:
            handler = self._ports.get(self.ANY_PORT)

        if handler is None:
            return False

        await handler._add_incoming_packet(packet)
        return True

    def bind(self, port: Port, handler: CspPortHandler) -> None:
        if isinstance(port, BindAnyPort):
            port = self.ANY_PORT

        if port in self._ports:
            raise ValueError('Port already bound')

        self._ports[port] = handler

    def unbind(self, port: Port) -> None:
        if isinstance(port, BindAnyPort):
            port = self.ANY_PORT
        del self._ports[port]

    def _find_free_port(self) -> int:
        for i in range(32, 64):  # TODO: global consts?
            if i not in self._ports:
                return i
            
        raise ValueError('No free port found')
