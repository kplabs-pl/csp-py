import asyncio
import csp_py

async def client_task(node: csp_py.CspNode):
    connection = await node.connect(dst=0, port=20)

    for i in range(0, 10):
        await connection.send(f'Hello, world! {i}'.encode('utf-8'))
        response = await connection.recv()
        print(f'Got response: {response.data.decode('utf-8')}')


async def server_task(node: csp_py.CspNode):
    socket = node.listen(20)

    while True:
        connection = await socket.accept()

        while True:
            packet = await connection.recv()
            await connection.send(b'Response to ' + packet.data)


async def main():
    node = csp_py.CspNode()

    router = asyncio.create_task(node.router.arun())
    server = asyncio.create_task(server_task(node))
    client = asyncio.create_task(client_task(node))

    await client

    server.cancel()
    router.cancel()


asyncio.run(main())
