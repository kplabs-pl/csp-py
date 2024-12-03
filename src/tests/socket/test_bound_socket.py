import asyncio

import pytest
from csp_py import CspNode, CspPacket
from csp_py.packet import CspId, CspPacketFlags


async def test_fail_to_bind_same_port_to_different_sockets(node: CspNode) -> None:
    node.bound_socket(30)

    with pytest.raises(ValueError):
        node.bound_socket(30)


async def test_can_bind_port_again_after_socket_destroyed(node: CspNode) -> None:
    socket1 = node.bound_socket(30)

    with pytest.raises(ValueError):
        node.bound_socket(30)

    socket1.close()

    node.bound_socket(30)


async def test_bound_socket_any_port(node: CspNode) -> None:
    server_sock = node.bound_socket(None)

    conn1 = await node.connect(dst=0, port=10)
    conn2 = await node.connect(dst=0, port=11)

    await conn1.send(b'abcd')
    await conn2.send(b'ghij')

    async with asyncio.timeout(1):
        packet1 = await server_sock.recv_from()
        packet2 = await server_sock.recv_from()

    assert packet1.data == b'abcd'
    assert packet1.packet_id.dport == 10
    assert packet2.data == b'ghij'
    assert packet2.packet_id.dport == 11


async def test_socket_bound_to_any_do_not_override_explicit_port(node: CspNode) -> None:
    explicit_port1 = node.bound_socket(10)
    any_port = node.bound_socket(None)
    explicit_port2 = node.bound_socket(11)
    client_socket = node.bound_socket(30)

    await client_socket.send_to(dst=0, port=10, data=b'abcd')
    await client_socket.send_to(dst=0, port=11, data=b'ghij')
    await client_socket.send_to(dst=0, port=15, data=b'klmn')
    await client_socket.send_to(dst=0, port=16, data=b'opqr')

    async with asyncio.timeout(1):
        packet1 = await explicit_port1.recv_from()
        packet2 = await explicit_port2.recv_from()
        packet3 = await any_port.recv_from()
        packet4 = await any_port.recv_from()

    assert packet1.data == b'abcd'
    assert packet2.data == b'ghij'
    assert packet3.data == b'klmn'
    assert packet4.data == b'opqr'


async def test_reply_using_bound_socket_on_any_port(node: CspNode) -> None:
    server_sock = node.bound_socket(None)
    client_sock = await node.connect(dst=0, port=10)

    await client_sock.send(b'abcd')
    server_packet = await server_sock.recv_from()
    await server_sock.send_reply(server_packet, b'ghij')

    async with asyncio.timeout(1):
        client_packet = await client_sock.recv()
    
    assert client_packet.data == b'ghij'


async def test_fail_to_send_on_bound_socket_on_any_port(node: CspNode) -> None:
    sock = node.bound_socket(None)

    with pytest.raises(AssertionError):
        await sock.send_to(dst=5, port=10, data=b'abcd')


async def test_bound_socket_send_reply_with_different_src_port(node: CspNode) -> None:
    sock = node.bound_socket(10)
    
    fake_request = CspPacket(
        packet_id=CspId(
            src=0,
            sport=11,
            dst=0,
            dport=11
        ),
        data=b'abcd'
    )
    with pytest.raises(ValueError):
        await sock.send_reply(fake_request, b'')


async def test_fail_to_bind_any_twice(node: CspNode) -> None:
    node.bound_socket(None)

    with pytest.raises(ValueError):
        node.bound_socket(None)


async def test_closing_socket_bound_to_any_allows_next_bound_to_any(node: CspNode) -> None:
    sock1 = node.bound_socket(None)

    with pytest.raises(ValueError):
        node.bound_socket(None)

    sock1.close()

    node.bound_socket(None)


async def test_bound_socket_use_explicit_flags(node: CspNode) -> None:
    recv_sock = node.bound_socket(10)
    sending_sock = node.bound_socket(11, send_flags=CspPacketFlags(8))
    await sending_sock.send_to(dst=0, port=10, data=b'abcd')

    msg = await recv_sock.recv_from()
    assert msg.packet_id.flags == CspPacketFlags(8)


async def test_bound_socket_use_inherit_by_default(node_with_flags: CspNode) -> None:
    recv_sock = node_with_flags.bound_socket(10)
    sending_sock = node_with_flags.bound_socket(11)
    await sending_sock.send_to(dst=0, port=10, data=b'abcd')

    msg = await recv_sock.recv_from()
    assert msg.packet_id.flags == CspPacketFlags(32)


async def test_bound_socket_use_mix_inherit_and_explicit(node_with_flags: CspNode) -> None:
    recv_sock = node_with_flags.bound_socket(10)
    sending_sock = node_with_flags.bound_socket(11, send_flags=CspPacketFlags(8) | CspPacketFlags.Inherit)
    await sending_sock.send_to(dst=0, port=10, data=b'abcd')

    msg = await recv_sock.recv_from()
    assert msg.packet_id.flags == CspPacketFlags(32) | CspPacketFlags(8)
