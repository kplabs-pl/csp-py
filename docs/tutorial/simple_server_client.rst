Simple server-client application
================================

Goal
----
This tutorial walks you through the creation of simple server-client application using Cubesat Space Protocol. We will use two ``asyncio`` tasks - one acting as client and second acting as server. For similarity with TCP sockets, connection-based model will be used.

Steps
-----

Application skeleton
++++++++++++++++++++
#. Start by creating empty skeleton for CSP application:

   .. code-block:: python

      import asyncio
      import csp_py
  
  
      async def main():
          node = csp_py.CspNode()
  
          router = asyncio.create_task(node.router.arun())

          # Rest of application goes here

          router.cancel()
  
  
      asyncio.run(main())

#. Add two empty (for now) tasks - one for server and one for client:

   .. code-block:: python
  
      async def client_task(node: csp_py.CspNode):
          pass
  
  
      async def server_task(node: csp_py.CspNode):
          pass
  
  
      async def main():
          node = csp_py.CspNode()
  
          router = asyncio.create_task(node.router.arun())
          server = asyncio.create_task(server_task(node))
          client = asyncio.create_task(client_task(node))
  
          await client
  
          server.cancel()
          router.cancel()

Client function
+++++++++++++++
#. In client task function, open connection to server on port 20

   .. code-block:: python
    
        async def client_task(node: csp_py.CspNode):
            connection = await node.connect(dst=0, port=20)

#. In loop, send packet to server

   .. code-block:: python

        async def client_task(node: csp_py.CspNode):
            connection = await node.connect(dst=0, port=20)

            for i in range(0, 10):
                await connection.send(f'Hello, world! {i}'.encode('utf-8'))

#. After sending packet, wait for response and print it

   .. code-block:: python

        async def client_task(node: csp_py.CspNode):
            connection = await node.connect(dst=0, port=20)

            for i in range(0, 10):
                await connection.send(f'Hello, world! {i}'.encode('utf-8'))
                response = await connection.recv()
                print(f'Got response: {response.data.decode('utf-8')}')

Server function
+++++++++++++++
#. Server task function starts by opening listening socket on port 20

   .. code-block:: python

        async def server_task(node: csp_py.CspNode):
            socket = node.listen(20)

#. Listening socket can be used to accept connections

   .. code-block:: python

        async def server_task(node: csp_py.CspNode):
            socket = node.listen(20)

            while True:
                connection = await socket.accept()

#. Using accepted connection, receive incoming packet

   .. code-block:: python

        async def server_task(node: csp_py.CspNode):
            socket = node.listen(20)

            while True:
                connection = await socket.accept()

                while True:
                    packet = await connection.recv()

#. Once packet is received, send response
   
   .. code-block:: python

        async def server_task(node: csp_py.CspNode):
            socket = node.listen(20)

            while True:
                connection = await socket.accept()

                while True:
                    packet = await connection.recv()
                    await connection.send(b'Response to ' + packet.data)

.. note:: Full source code for this tutorial can be found in ``examples/simple_server_client.py``.

Running
+++++++

#. Execute the application:

   .. code-block:: shell-session

      shell$ python examples/simple_server_client.py
      Got response: Response to Hello, world! 0
      Got response: Response to Hello, world! 1
      Got response: Response to Hello, world! 2
      Got response: Response to Hello, world! 3
      Got response: Response to Hello, world! 4
      Got response: Response to Hello, world! 5
      Got response: Response to Hello, world! 6
      Got response: Response to Hello, world! 7
      Got response: Response to Hello, world! 8
      Got response: Response to Hello, world! 9

    Client got response from server for each packet sent.

Summary
-------
In this example we've create very simple client-server application using Cubesat Space Protocol. Client task used ``CspNode.connect`` function to establish connection while server followed TCP-like model with ``CspNode.listen`` and ``CspSocket.accept`` functions. Both client and server used ``send`` and ``recv`` functions on their respective connections to send and receive packets.
