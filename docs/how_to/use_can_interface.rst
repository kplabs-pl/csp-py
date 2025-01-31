Use CAN interface
=================

This guide will show you how to use the CAN interface in CSP.py. The CAN (Controller Area Network) interface allows microcontrollers and devices to communicate with each other without a host computer.
The ``CspCanInterface`` in CSP.py handles communication over a CAN bus. It fragments and reassembles packets to fit within the constraints of CAN frames. This interface is useful for applications that require robust and reliable communication between devices in a network.

Prerequisites
-------------

- Basic tutorial completed (:ref:`simple_server_client`)

1. **Adding the CAN Interface**:
    The CAN interface is added to the router using the ``add_interface`` method. Each interface is associated with an address and a network mask.

    .. code-block:: python

        can_interface = CspCanInterface()

        node.router.add_interface(can_interface, address=0x100, netmask_bits=6)

2. **Sending and Receiving Packets**:
    Use the CAN interface to send and receive packets. The interface handles the fragmentation and reassembly of packets to fit within CAN frames.

    .. code-block:: python

        async def send_packet(node: CspNode):
            connection = await node.connect(dst=0x200, port=10)
            await connection.send(b'Hello, CAN!')

        async def receive_packet(node: CspNode):
            socket = node.listen(10)
            connection = await socket.accept()
            packet = await connection.recv()
            print(f'Received: {packet.data.decode()}')
