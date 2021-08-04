This module adds `UPS <https://ups.com>`_ to the available carriers.

It allows you to register shippings, generate labels, get rates from order, read
shipping states and cancel shipments using UPS webservice, so no need of exchanging
any kind of file.

When a sales order is created in Odoo and the UPS carrier is assigned, the shipping
price that will be obtained will be the price that the UPS webservice estimates
according to the order information (address and products).
