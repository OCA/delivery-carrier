[![Build Status](https://travis-ci.org/OCA/carrier-delivery.svg?branch=9.0)](https://travis-ci.org/OCA/carrier-delivery)
[![Coverage Status](https://coveralls.io/repos/OCA/carrier-delivery/badge.svg?branch=9.0)](https://coveralls.io/r/OCA/carrier-delivery?branch=9.0)

Carriers And Deliveries Management
==================================

This project aim to deal with modules related to manage carriers and deliveries in a generic way.

You'll find:

 - Generic module to generate file for carrier
 - Specific implementation for specific carrier (like la poste, tnt,..)
 - Generation of shipping labels for specific carrier (PostLogistics, ...)

[//]: # (addons)

Available addons
----------------
addon | version | summary
--- | --- | ---
[base_delivery_carrier_label](base_delivery_carrier_label/) | 9.0.1.0.0 | Base module for carrier labels
[delivery_carrier_deposit](delivery_carrier_deposit/) | 9.0.0.1.0 | Create deposit slips
[delivery_carrier_label_postlogistics](delivery_carrier_label_postlogistics/) | 9.0.1.1.0 | PostLogistics Labels WebService
[stock_picking_delivery_rate](stock_picking_delivery_rate/) | 9.0.1.0.0 | Adds a concept of rate quotes for stock pickings


Unported addons
---------------
addon | version | summary
--- | --- | ---
[base_delivery_carrier_files](base_delivery_carrier_files/) | 1.2.3 (unported) | Base Delivery Carrier Files
[base_delivery_carrier_files_document](base_delivery_carrier_files_document/) | 1.0.1 (unported) | Base module for picking carrier files creation for document
[delivery_carrier_b2c](delivery_carrier_b2c/) | 8.0.0.2.0 (unported) | Delivery Carrier Business To Customer
[delivery_carrier_file_laposte](delivery_carrier_file_laposte/) | 1.0 (unported) | Delivery Carrier File: La Poste
[delivery_carrier_file_tnt](delivery_carrier_file_tnt/) | 1.0 (unported) | Delivery Carrier File: TNT
[delivery_carrier_label_default_webkit](delivery_carrier_label_default_webkit/) | 1.0 (unported) | Module for carrier labels
[delivery_carrier_label_dispatch](delivery_carrier_label_dispatch/) | 1.0 (unported) | Carrier labels - Picking dispatch (link)
[delivery_carrier_label_gls](delivery_carrier_label_gls/) | 0.1 (unported) | GLS carrier label printing
[delivery_carrier_label_postlogistics_shop_logo](delivery_carrier_label_postlogistics_shop_logo/) | 1.0 (unported) | PostLogistics labels - logo per Shop
[delivery_optional_invoice_line](delivery_optional_invoice_line/) | 0.1 (unported) | Delivery Optional Invoice Line

[//]: # (end addons)

Translation Status
------------------
[![Transifex Status](https://www.transifex.com/projects/p/OCA-carrier-delivery-9-0/chart/image_png)](https://www.transifex.com/projects/p/OCA-carrier-delivery-9-0)
