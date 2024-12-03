import asyncio

import pytest
from csp_py import CspNode
from csp_py.packet import CspPacketFlags
from csp_py.socket import CspClientConnection


async def test_closing_connection_frees_local_port(node: CspNode) -> None:
    connection = await node.connect(dst=0, port=10, local_port=40)

    with pytest.raises(ValueError):
        node.bound_socket(40)

    connection.close()

    node.bound_socket(40) 


async def test_fail_to_open_two_connections_on_same_local_port(node: CspNode) -> None:
    await node.connect(dst=0, port=10, local_port=40)

    with pytest.raises(ValueError):
        await node.connect(dst=0, port=11, local_port=40)


async def test_multiple_connections(node: CspNode) -> None:
    server_socket = node.listen(30)

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

    server_side_task = asyncio.create_task(server_side())

    client_conn1 = await node.connect(dst=0, port=30, local_port=40)
    client_conn2 = await node.connect(dst=0, port=30, local_port=41)

    async def exchange(conn: CspClientConnection, msgs: list[bytes]) -> None:
        async with asyncio.timeout(1):
            for msg in msgs:
                await conn.send(msg)
                response = await conn.recv()
                assert response.data == msg

    await exchange(client_conn1, [b'Hello', b'World'])
    await exchange(client_conn2, [b'Baz', b'Qux'])


    server_side_task.cancel()


async def test_client_connection_drop_packets_from_unexpected_remote(node: CspNode) -> None:
    connection = await node.connect(dst=0, port=10, local_port=20)
    sock1 = node.bound_socket(11)
    sock2 = node.bound_socket(10)

    # send packet to connection's local port but from unexpected source port
    await sock1.send_to(dst=0, port=20, data=b'abcd')
    await sock2.send_to(dst=0, port=20, data=b'ghij')

    async with asyncio.timeout(0.1):
        packet = await connection.recv()

    assert packet.data == b'ghij'


async def test_access_pending_packets_after_accepting_connection(node: CspNode) -> None:
    listening_sock = node.listen(10)
    client_connection = await node.connect(dst=0, port=10, local_port=20)
    await client_connection.send(b'abcd')
    await client_connection.send(b'ghij')

    server_connection = await listening_sock.accept()
    async with asyncio.timeout(1):
        packet1 = await server_connection.recv()
        packet2 = await server_connection.recv()

    assert packet1.data == b'abcd'
    assert packet2.data == b'ghij'


async def test_fail_to_listen_twice_on_same_local_port(node: CspNode) -> None:
    node.listen(10)

    with pytest.raises(ValueError):
        node.listen(10)


async def test_closing_listening_socket_frees_local_port(node: CspNode) -> None:
    sock = node.listen(10)

    with pytest.raises(ValueError):
        node.listen(10)

    sock.close()

    node.listen(10)


async def test_closing_server_connection_with_pending_packets_drops_them(node: CspNode) -> None:
    listening_sock = node.listen(10)
    client_connection = await node.connect(dst=0, port=10, local_port=20)
    await client_connection.send(b'abcd')
    await client_connection.send(b'ghij')

    server_connection = await listening_sock.accept()
    await server_connection.recv()

    # one packet received, one still pending in connection
    server_connection.close()

    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.1):
            server_connection = await listening_sock.accept()


async def test_connect_with_auto_local_port(node: CspNode) -> None:
    node.bound_socket(32)
    node.bound_socket(33)
    node.bound_socket(35)
    listening_sock = node.listen(5)
    client_connection = await node.connect(dst=0, port=5)
    await client_connection.send(b'abcd')
    server_connection = await listening_sock.accept()
    packet = await server_connection.recv()

    assert packet.packet_id.sport == 34


async def test_listen_on_any_port(node: CspNode) -> None:
    server_sock = node.listen(None)
    conn1 = await node.connect(dst=0, port=10)
    conn2 = await node.connect(dst=0, port=11)

    await conn1.send(b'abcd')
    await conn2.send(b'ghij')

    async with asyncio.timeout(2):
        server_conn1 = await server_sock.accept()
        assert server_conn1.remote_address == 0
        assert server_conn1.local_port == 10
        packet1 = await server_conn1.recv()
        assert packet1.data == b'abcd'

        server_conn2 = await server_sock.accept()
        assert server_conn2.remote_address == 0
        assert server_conn2.local_port == 11
        packet2 = await server_conn2.recv()
        assert packet2.data == b'ghij'


async def test_respond_using_listen_on_any_port(node: CspNode) -> None:
    server_sock = node.listen(None)
    client_conn = await node.connect(dst=0, port=10)

    await client_conn.send(b'abcd')

    server_conn = await server_sock.accept()
    await server_conn.send(b'ghij')

    async with asyncio.timeout(1):
        packet = await client_conn.recv()

    assert packet.data == b'ghij'


async def test_listen_with_explicit_flags(node: CspNode) -> None:
    server_sock = node.listen(10, send_flags=CspPacketFlags(8))
    client_sock = await node.connect(dst=0, port=10)

    await client_sock.send(b'abcd')
    server_conn = await server_sock.accept()
    await server_conn.recv()
    await server_conn.send(b'ghij')

    response = await client_sock.recv()
    assert response.packet_id.flags == CspPacketFlags(8)


async def test_listen_use_inherit_flags_by_default(node_with_flags: CspNode) -> None:
    server_sock = node_with_flags.listen(10)
    client_sock = await node_with_flags.connect(dst=0, port=10)

    await client_sock.send(b'abcd')
    server_conn = await server_sock.accept()
    await server_conn.recv()
    await server_conn.send(b'ghij')

    response = await client_sock.recv()
    assert response.packet_id.flags == CspPacketFlags(32)


async def test_listen_use_mix_inherit_and_explicit(node_with_flags: CspNode) -> None:
    server_sock = node_with_flags.listen(10, send_flags=CspPacketFlags(8) | CspPacketFlags.Inherit)
    client_sock = await node_with_flags.connect(dst=0, port=10)

    await client_sock.send(b'abcd')
    server_conn = await server_sock.accept()
    await server_conn.recv()
    await server_conn.send(b'ghij')

    response = await client_sock.recv()
    assert response.packet_id.flags == CspPacketFlags(32) | CspPacketFlags(8)


async def test_connect_with_explicit_flags(node: CspNode) -> None:
    server_sock = node.bound_socket(10)
    client_sock = await node.connect(dst=0, port=10, send_flags=CspPacketFlags(8))
    await client_sock.send(b'abcd')

    msg = await server_sock.recv_from()

    assert msg.packet_id.flags == CspPacketFlags(8)


async def test_connect_use_inherit_flags_by_default(node_with_flags: CspNode) -> None:
    server_sock = node_with_flags.bound_socket(10)
    client_sock = await node_with_flags.connect(dst=0, port=10)
    await client_sock.send(b'abcd')

    msg = await server_sock.recv_from()

    assert msg.packet_id.flags == CspPacketFlags(32)


async def test_connect_use_mix_inherit_and_explicit(node_with_flags: CspNode) -> None:
    server_sock = node_with_flags.bound_socket(10)
    client_sock = await node_with_flags.connect(dst=0, port=10, send_flags=CspPacketFlags(8) | CspPacketFlags.Inherit)
    await client_sock.send(b'abcd')

    msg = await server_sock.recv_from()

    assert msg.packet_id.flags == CspPacketFlags(32) | CspPacketFlags(8)
