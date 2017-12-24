[![Build Status](https://travis-ci.org/OCA/delivery-carrier.svg?branch=10.0)](https://travis-ci.org/OCA/delivery-carrier)
[![Coverage Status](https://coveralls.io/repos/OCA/delivery-carrier/badge.svg?branch=10.0)](https://coveralls.io/r/OCA/delivery-carrier?branch=10.0)

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
[base_delivery_carrier_label](base_delivery_carrier_label/) | 10.0.1.1.0 | Base module for carrier labels
[delivery_carrier_b2c](delivery_carrier_b2c/) | 10.0.0.1.0 | Delivery Carrier Business To Customer
[delivery_multi_destination](delivery_multi_destination/) | 10.0.1.1.0 | Multiple destinations for the same delivery method
[sale_delivery_rate](sale_delivery_rate/) | 10.0.1.0.0 | Extends notion of delivery carrier rate quotes to sale orders
[stock_picking_delivery_rate](stock_picking_delivery_rate/) | 10.0.1.0.0 | Adds a concept of rate quotes for stock pickings


Unported addons
---------------
addon | version | summary
--- | --- | ---
[base_delivery_carrier_files](base_delivery_carrier_files/) | 1.2.3 (unported) | Base Delivery Carrier Files
[base_delivery_carrier_files_document](base_delivery_carrier_files_document/) | 1.0.1 (unported) | Base module for picking carrier files creation for document
[delivery_carrier_deposit](delivery_carrier_deposit/) | 8.0.0.2.0 (unported) | Create deposit slips
[delivery_carrier_file_laposte](delivery_carrier_file_laposte/) | 1.0 (unported) | Delivery Carrier File: La Poste
[delivery_carrier_file_tnt](delivery_carrier_file_tnt/) | 1.0 (unported) | Delivery Carrier File: TNT
[delivery_carrier_label_default_webkit](delivery_carrier_label_default_webkit/) | 1.0 (unported) | Module for carrier labels
[delivery_carrier_label_dispatch](delivery_carrier_label_dispatch/) | 1.0 (unported) | Carrier labels - Picking dispatch (link)
[delivery_carrier_label_gls](delivery_carrier_label_gls/) | 0.1 (unported) | GLS carrier label printing
[delivery_carrier_label_postlogistics](delivery_carrier_label_postlogistics/) | 9.0.1.1.0 (unported) | PostLogistics Labels WebService
[delivery_carrier_label_postlogistics_shop_logo](delivery_carrier_label_postlogistics_shop_logo/) | 1.0 (unported) | PostLogistics labels - logo per Shop
[delivery_optional_invoice_line](delivery_optional_invoice_line/) | 0.1 (unported) | Delivery Optional Invoice Line

[//]: # (end addons)

Translation Status
------------------
[![Transifex Status](https://www.transifex.com/projects/p/OCA-carrier-delivery-10-0/chart/image_png)](https://www.transifex.com/projects/p/OCA-carrier-delivery-10-0)
