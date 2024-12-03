import asyncio

from csp_py import CspNode, CspPacket
from csp_py.interfaces.interface_pair import InterfacePair
from csp_py.packet import CspId, CspPacketFlags
from csp_py.socket import CspClientConnection, CspSocketHandler


async def test_socket(node: CspNode) -> None:
    socket1 = node.bound_socket(30)
    socket2 = node.bound_socket(40)

    await socket2.send_to(dst=0, port=30, data=b'Hello, world!')
    async with asyncio.timeout(1):
        packet: CspPacket = await socket1.recv_from()

        assert packet.packet_id.src == 0
        assert packet.packet_id.sport == 40
        assert packet.packet_id.dst == 0
        assert packet.packet_id.dport == 30
        assert packet.data == b'Hello, world!'


async def test_send_with_connection(node: CspNode) -> None:
    socket1 = node.bound_socket(30)

    conn = await node.connect(dst=0, port=30, local_port=40)
    await conn.send(b'Hello, world!')

    async with asyncio.timeout(1):
        packet: CspPacket = await socket1.recv_from()

        assert packet.packet_id.src == 0
        assert packet.packet_id.sport == 40
        assert packet.packet_id.dst == 0
        assert packet.packet_id.dport == 30
        assert packet.data == b'Hello, world!'


async def test_recv_with_connection(node: CspNode) -> None:
    socket1 = node.bound_socket(30)

    conn = await node.connect(dst=0, port=30, local_port=40)
    await conn.send(b'Hello, world!')
    request = await socket1.recv_from()
    await socket1.send_reply(request, b'Hello, back!')

    async with asyncio.timeout(1):
        response = await conn.recv()

        assert response.packet_id.src == 0
        assert response.packet_id.sport == 30
        assert response.packet_id.dst == 0
        assert response.packet_id.dport == 40
        assert response.data == b'Hello, back!'


async def test_accept_connection(node: CspNode) -> None:
    socket1 = node.listen(30)

    async def client_side() -> None:
        conn = await node.connect(dst=0, port=30, local_port=40)
        await conn.send(b'Hello, world!')
        response = await conn.recv()

        assert response.packet_id.src == 0
        assert response.packet_id.sport == 30
        assert response.packet_id.dst == 0
        assert response.packet_id.dport == 40

    async def server_side() -> None:
        conn = await socket1.accept()
        await conn.recv()
        await conn.send(b'Hello, back!')

    async with asyncio.timeout(1):
        await asyncio.gather(
            asyncio.create_task(client_side()),
            asyncio.create_task(server_side()),
        )


async def test_socket_reply(node: CspNode) -> None:
    socket1 = node.bound_socket(30)
    socket2 = node.bound_socket(40)

    await socket2.send_to(dst=0, port=30, data=b'Hello, world!')
    async with asyncio.timeout(1):
        packet1: CspPacket = await socket1.recv_from()
        await socket1.send_reply(packet1, b'Hello, back!')

    async with asyncio.timeout(1):
        packet2: CspPacket = await socket2.recv_from()

        assert packet2.packet_id.src == 0
        assert packet2.packet_id.sport == 30
        assert packet2.packet_id.dst == 0
        assert packet2.packet_id.dport == 40
        assert packet2.data == b'Hello, back!'


async def test_connection_between_nodes() -> None:
    server_node = CspNode()
    client_node1 = CspNode()
    client_node2 = CspNode()

    client1_to_server = InterfacePair()
    client2_to_server = InterfacePair()

    client_node1.router.add_interface(client1_to_server.iface1, address=0x110, netmask_bits=6)
    client_node2.router.add_interface(client2_to_server.iface1, address=0x210, netmask_bits=6)
    server_node.router.add_interface(client1_to_server.iface2, address=0x111, netmask_bits=6)
    server_node.router.add_interface(client2_to_server.iface2, address=0x211, netmask_bits=6)

    server_router_task = asyncio.create_task(server_node.router.arun())
    client1_router_task = asyncio.create_task(client_node1.router.arun())
    client2_router_task = asyncio.create_task(client_node2.router.arun())

    server_socket = server_node.listen(30)

    async def server_side() -> None:
        client_tasks: list[asyncio.Task[None]] = []

        try:
            while True:
                conn = await server_socket.accept()

                async def conn_handler() -> None:
                    try:
                        while True:
                            msg = await conn.recv()
                            await conn.send(msg.data)
                    except asyncio.CancelledError:
                        pass
                
                client_tasks.append(asyncio.create_task(conn_handler()))
        except asyncio.CancelledError:
            for ct in client_tasks:
                ct.cancel()
                try:
                    await ct
                except asyncio.CancelledError:
                    pass

    server_side_task = asyncio.create_task(server_side())

    async def exchange(conn: CspClientConnection, msgs: list[bytes]) -> None:
        async with asyncio.timeout(1):
            for msg in msgs:
                await conn.send(msg)
                response = await conn.recv()
                assert response.data == msg


    client_conn1 = await client_node1.connect(dst=0x111, port=30, local_port=40)
    client_conn2 = await client_node2.connect(dst=0x211, port=30, local_port=40)

    await exchange(client_conn1, [b'Hello', b'World'])
    await exchange(client_conn2, [b'Baz', b'Qux'])

    server_side_task.cancel()
    try:
        await server_side_task
    except asyncio.CancelledError:
        pass

    server_router_task.cancel()
    client1_router_task.cancel()
    client2_router_task.cancel()


async def test_ignore_packet_not_going_to_socket() -> None:
    handler = CspSocketHandler()
    handler.bound_socket(30, send_flags=CspPacketFlags.Zero)

    r = await handler.on_packet(CspPacket(
        packet_id=CspId(
            src=10,
            dst=20,
            dport=31,
            sport=30,
        )
    ))

    assert r == False
