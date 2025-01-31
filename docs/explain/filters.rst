Filters
=======

Filters in CSP.py are mechanisms that allow you to process, modify, or drop packets as they are routed through the system. Filters can be applied to incoming, routed, and outgoing packets, providing a flexible way to handle packet processing based on specific criteria.

User can create custom filters to perform tasks such as checksum validation, encryption, or logging. Filters can be registered with the ``CspRouter`` instance and applied to packets during the routing process.

There are several built-in filters available in CSP.py, including:
    - CRC32 filters for checksum validation.
    - Routing filters for managing packet routing based on specific criteria.

Every outgoing or incoming packet which is processed by the router is passed through the filters. The filters can be used to modify the packet, drop it, or perform other actions based on the filter's logic.

Filters are defined as callable functions which takes a ``CspPacket`` packet, process it and then returns filtered packet. The filter can also return ``None`` to drop the packet.

Filters are applied one by one in the order passed to the list holding registered filters, kept in the ``CspRouter``.
