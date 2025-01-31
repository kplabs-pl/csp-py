CSP OSI Architecture
====================

Overview
--------

The Cubesat Space Protocol (CSP) is a small network-layer delivery protocol designed for use in space applications. It provides a lightweight and efficient way to handle communication between nodes in a network, making it ideal for use in resource-constrained environments such as small satellites and other space-based systems. CSP is designed to be simple and easy to implement, ensuring that it can be used in a wide range of applications.

CSP follows a layered architecture similar to the Open Systems Interconnection (OSI) model. Each layer serves a specific function and interacts with the layers directly above and below it.

CSP Layers
----------

CSP is typically implemented using a simplified version of the OSI model, focusing on the most relevant layers for space communication. The key layers in CSP are:

1. **Physical Layer**:
    - The physical layer is responsible for the actual transmission of raw data bits over a physical medium. In CSP, this could be a radio frequency (RF) link, a wired connection, or any other medium suitable for space communication.

2. **Data Link Layer**:
    - The data link layer provides node-to-node data transfer and handles error detection and correction. It ensures that data sent from the physical layer is free of errors and properly framed. In CSP, this layer may include protocols for framing, addressing, and error checking.

3. **Network Layer**:
    - The network layer is responsible for packet forwarding, including routing through intermediate nodes. CSP's network layer handles addressing, packet forwarding, and routing decisions to ensure that packets reach their intended destination.

4. **Transport Layer**:
    - The transport layer provides end-to-end communication services for applications. It ensures that data is delivered reliably and in the correct order. CSP's transport layer may include mechanisms for connection-oriented communication, flow control, and error recovery.

5. **Application Layer**:
    - The application layer is the topmost layer and provides network services directly to the end-users or applications. In CSP, this layer includes various application-specific protocols and services, such as telemetry, telecommand, and data transfer.


See more: https://libcsp.github.io/libcsp/basic.html