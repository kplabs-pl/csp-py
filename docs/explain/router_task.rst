Router Task
===========

In CSP.py, the :term:`Router` (``CspRouter``) is a main component responsible for managing the routing of packets between different interfaces and ensuring that packets reach their intended destinations.
The router task operates asynchronously, processing incoming packets and determining the appropriate actions based on the packet's destination.

``CspRouter`` holds several properties:

    .. list-table::
        :widths: 20 80
        :header-rows: 1

        * - Property
          - Description
        * - ``interfaces``
          - A list of interfaces that the router will use to send and receive packets.
        * - ``incoming packets queue``
          - A queue that holds incoming packets waiting to be processed by the router.
        * - ``routing table``
          - A table that defines the routing rules for packets, including destination addresses and associated interfaces.
        * - ``incoming filters``
          - A list of filters that will be applied to incoming packets before they are processed by the router.
        * - ``outgoing filters``
          - A list of filters that will be applied to outgoing packets before they are sent to the interfaces.
        * - ``routed filters``
          - A list of filters that will be applied to packets that are routed through the system.
  
Router Logic
------------

When handling packets, Router logic includes the following steps:
    - Receive incoming packets from the interfaces and place them in the incoming packets queue.
    - Process each packet in the queue by applying the incoming filters to determine if the packet should be modified, dropped, or passed to the routing logic.
    - Determine the appropriate interface for the packet based on its destination address and the routing table.
    - Apply the routed filters to the packet before sending it to the selected interface.
    - Send the packet to the selected interface for transmission.
