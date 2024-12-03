import time

from ..node import CspNode
from ..packet import CspPacketFlags


async def ping(node: CspNode, *, dst: int, size: int = 100, send_flags: CspPacketFlags = CspPacketFlags.Inherit) -> float:
    sock = await node.connect(dst=dst, port=1, send_flags=send_flags)
    data = bytes([i % 256 for i in range(size)])
    
    start = time.monotonic()
    await sock.send(data)
    response = await sock.recv()
    stop = time.monotonic()
    assert response.data == data, f'{response!r} != {data!r}'
    return stop - start
