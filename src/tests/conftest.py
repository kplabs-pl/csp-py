import asyncio
from typing import AsyncIterator
import pytest

from csp_py import CspNode
from csp_py.packet import CspPacketFlags

from .support import CspRouterTest


@pytest.fixture
def router() -> CspRouterTest:
    return CspRouterTest()


@pytest.fixture
async def node() -> AsyncIterator[CspNode]:
    node = CspNode()
    router_task = asyncio.create_task(node.router.arun())
    try:
        yield node
    finally:
        router_task.cancel()
        try:
            await router_task
        except asyncio.CancelledError:
            pass

@pytest.fixture
async def node_with_flags() -> AsyncIterator[CspNode]:
    node = CspNode(default_send_flags=CspPacketFlags(32))
    router_task = asyncio.create_task(node.router.arun())
    try:
        yield node
    finally:
        router_task.cancel()
        try:
            await router_task
        except asyncio.CancelledError:
            pass