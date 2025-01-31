Route Packets Indirectly
========================

This tutorial demonstrates how to route packets indirectly using the Cubesat Space Protocol (CSP). By setting up routing tables and interfaces, you can control the path packets take through the network.
In CSP.py, routing tables and interfaces are used to manage the flow of packets between nodes. By configuring these components, you can ensure that packets are routed through specific paths, even if they are not directly connected.

Prerequisites
-------------

- Basic tutorial completed (:ref:`simple_server_client`)

Steps
-----

1. **Create a CSP Node and Add Interface**:
    Initialize a ``CspNode`` instance and add interfaces to it.

    .. code-block:: python

        import asyncio
        import csp_py

        async def main():
            node = csp_py.CspNode()
            lo_interface = csp_py.interfaces.LoInterface()
            can_interface = csp_py.interfaces.CanInterface()
            node.router.add_interface(lo_interface, address=0, netmask_bits=6)
            node.router.add_interface(can_interface, address=0x0100, netmask_bits=6)


2. **Add Routing Table Entries**:
    Add entries to the routing table to define indirect routes.

    .. code-block:: python

        node.router.rtable.add_entry(network_address=0x0100, netmask_bits=6, iface=lo_interface)
        node.router.rtable.add_entry(network_address=0x0200, netmask_bits=6, iface=can_interface)

    In above code snippet we are adding two entries to the routing table. The first entry routes packets with a network address of `0x0100` through the `lo_interface`, and the second entry routes packets with a network address of `0x0200` through the `can_interface`. The `netmask_bits` parameter specifies the number of bits in the network mask, which determines how many addresses are included in the route.

3. **Send Packets Using Indirect Routes**:
    Use the node to send packets that will be routed indirectly.

    .. code-block:: python

        async def send_packet(node: csp_py.CspNode):
            connection = await node.connect(dst=0x0200, port=10)
            await connection.send(b'Hello, indirect route!')

        In this example, we are sending a packet to the destination address `0x0200` using the `send_packet` function. The packet will be routed through the `can_interface` as defined in the routing table.

.. note::
    Keep in mind that each entry in the routing table that contains defined address and netmask with associated interface should be unique.
    If user tries to add new entry which overlaps with existing entry, it will raise an error.
