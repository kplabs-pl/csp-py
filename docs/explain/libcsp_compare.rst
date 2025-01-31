Comparison to LibCSP
====================

Goal
----

This document provides a comparison between CSP.py and LibCSP, highlighting the differences, advantages, and considerations of using each implementation. Understanding these differences can help you choose the right tool for your specific needs.

Explanation
-----------

LibCSP is the original implementation of the Cubesat Space Protocol (CSP) written in C. It is widely used in embedded systems and space applications due to its efficiency and low resource consumption. CSP.py is a Python implementation of the same protocol, designed to offer ease of use, readability, and flexibility.

Key Differences
---------------

1. **Language**:
    - **LibCSP**: Written in C, which is a low-level language known for its performance and control over hardware resources.
    - **CSP.py**: Written in Python, a high-level language known for its readability and ease of use.

2. **Performance**:
    - **LibCSP**: Offers high performance and low latency, making it suitable for resource-constrained environments such as embedded systems.
    - **CSP.py**: While not as performant as C, Python's performance is sufficient for many applications, especially those not constrained by real-time requirements.

3. **Ease of Use**:
    - **LibCSP**: Requires knowledge of C and low-level programming concepts, which can be challenging for beginners.
    - **CSP.py**: Python's simplicity and readability make it accessible to a broader audience, including those new to programming.

4. **Development Speed**:
    - **LibCSP**: Development can be slower due to the complexity of C and the need for manual memory management.
    - **CSP.py**: Python's high-level abstractions and dynamic typing allow for faster development and prototyping.

5. **Community and Ecosystem**:
    - **LibCSP**: Has a strong community in the embedded systems and space industry, with extensive documentation and support.
    - **CSP.py**: Benefits from Python's large and active community, with access to a wide range of libraries and tools.

6. **Portability**:
    - **LibCSP**: Highly portable across different hardware platforms, including microcontrollers and space-grade processors.
    - **CSP.py**: Portable across different operating systems, but may require additional work to run on resource-constrained devices.

How-to Guide
------------

Choosing Between LibCSP and CSP.py

1. **Consider Your Application Requirements**:
    - If your application requires high performance, low latency, and runs on resource-constrained devices, LibCSP may be the better choice.
    - If your application benefits from rapid development, ease of use, and runs on general-purpose computers, CSP.py may be more suitable.

2. **Evaluate Your Team's Expertise**:
    - If your team has experience with C and low-level programming, leveraging LibCSP's performance advantages may be beneficial.
    - If your team is more comfortable with Python or needs to quickly prototype and iterate, CSP.py's simplicity can be advantageous.

3. **Assess the Development Environment**:
    - For embedded systems and space applications, LibCSP's efficiency and control over hardware resources are critical.
    - For applications in research, education, or general software development, CSP.py's readability and extensive ecosystem can accelerate progress.

Example Usage
-------------

Here is an example of how to set up a simple server-client application using CSP.py, demonstrating its ease of use and readability:

1. **Set Up the Application Skeleton**:
    .. code-block:: python

        import asyncio
        import csp_py

        async def main():
            node = csp_py.CspNode()
            router_task = asyncio.create_task(node.router.arun())
            await router_task

        asyncio.run(main())

2. **Send and Receive Packets**:
    .. code-block:: python

        async def send_packet(node: csp_py.CspNode):
            connection = await node.connect(dst=0, port=10)
            await connection.send(b'Hello, CSP!')

        async def receive_packet(node: csp_py.CspNode):
            socket = node.listen(10)
            connection = await socket.accept()
            packet = await connection.recv()
            print(f'Received: {packet.data.decode()}')

Summary
-------

Both LibCSP and CSP.py have their strengths and are suited to different types of applications. LibCSP excels in performance and is ideal for embedded systems and space applications, while CSP.py offers ease of use, rapid development, and a rich ecosystem, making it suitable for a wide range of other applications. By understanding the differences and evaluating your specific needs, you can choose the right implementation for your project.