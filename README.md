![PyPI - Version](https://img.shields.io/pypi/v/cubesat-space-protocol-py)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/kplabs-pl/csp-py/build.yml)


CSP.py
===
Native Python, async-friendly implementation of Cubesat Space Protocol.

# Features
* Python friendly async API
* Sockets and connections
* Interfaces
    * CAN Fragmentation Protocol v2 (compatible with https://github.com/libcsp/libcsp)
    * Serializing interface for easy intergration with other applications
    * Interface pair for in-memory testing between two nodes
* Socket options
    * CRC32 (compatible with https://github.com/libcsp/libcsp)
* CIDR Routing table
* Hooks for inspecting and/or modifying packets going through node
* System services
    * Ping


## Missing features compared to libcsp
* RDP
* Packet flags
    * HMAC
* Remaining system sevices: uptime, reboot/shutdown, process list, memory free query, CSP Management Protocol
* Simple fragmentation protocol

# When to use over libcsp?
* Easy use (pure Python library, no native dependencies)
* Testing
    * `csp-py` allows to start and tear down entire node within single test without leaking anything between tests
* Async API
    * Use `asyncio` to run communication, with gracefully handled timeouts and cancellations

# Usage
1. Install package using `pip`
    ```console
    user$ pip install cubesat-space-protocol-py
    ```
2. Create node:
    ```python
    import csp_py

    node = csp_py.CspNode()
    ```
3. Add interface
    ```python
    from csp_py.interfaces.serializing_interface import CspSerializingInterface

    async def capture_frame(frame: bytes) -> None:
        # TODO: frame contains entire serialized packet including header
        # send it over some communication channel
        pass

    async def handle_incoming_frames(iface: CspSerializingInterface) -> None:
        while True:
            # TODO: fetch frame from communication channel
            frame: bytes = await recv_frame()
            await iface.on_incoming_frame(frame)

    iface = CspSerializingInterface(capture_frame)
    # TODO: make sure addresses are correct
    node.router.add_interface(iface, address=1, netmask_bits=10)
    asyncio.create_task(handle_incoming_frames(iface))
    ```
4. Start router task
    ```python
    router_task = asyncio.create_task(node.router.arun())
    ```
5. Use sockets
    ```python
    connection = await node.connect(dst=0, port=20)
    await connection.send(b'Hello, world!')
    response = await connection.recv()
    print(f'Got response: {response.data}')
    ```
6. Stop router
    ```python
    router_task.cancel()
    await router_task
    ```
