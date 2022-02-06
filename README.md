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
addon | version | maintainers | summary
--- | --- | --- | ---
[base_delivery_carrier_files](base_delivery_carrier_files/) | 10.0.1.0.2 |  | Base module for creation of delivery carrier files
[base_delivery_carrier_files_document](base_delivery_carrier_files_document/) | 10.0.1.0.1 |  | Allow to store carrier files as attachments. Auto-install when the module Document and Base Delivery Carrier Files are installed.
[base_delivery_carrier_label](base_delivery_carrier_label/) | 10.0.1.3.1 |  | Base module for carrier labels
[delivery_auto_refresh](delivery_auto_refresh/) | 10.0.1.0.0 |  | Auto-refresh delivery price in sales orders
[delivery_carrier_b2c](delivery_carrier_b2c/) | 10.0.0.1.0 |  | Delivery Carrier Business To Customer
[delivery_carrier_category](delivery_carrier_category/) | 10.0.1.1.0 | [![rousseldenis](https://github.com/rousseldenis.png?size=30px)](https://github.com/rousseldenis) | Adds a category to delivery carriers in order to help users classifying them
[delivery_carrier_default_tracking_url](delivery_carrier_default_tracking_url/) | 10.0.1.1.0 | [![rousseldenis](https://github.com/rousseldenis.png?size=30px)](https://github.com/rousseldenis) | Adds the default tracking url on delivery carrier
[delivery_carrier_deposit](delivery_carrier_deposit/) | 10.0.0.2.0 |  | Create deposit slips
[delivery_carrier_file_tnt](delivery_carrier_file_tnt/) | 10.0.1.0.1 |  | Sub-module for Base Delivery Carrier Files. Definition of the delivery carrier file for "TNT Express Shipper".
[delivery_carrier_label_default](delivery_carrier_label_default/) | 10.0.1.0.1 |  | Default label for carrier labels
[delivery_carrier_label_postlogistics](delivery_carrier_label_postlogistics/) | 10.0.1.2.1 |  | Print postlogistics shipping labels
[delivery_carrier_partner](delivery_carrier_partner/) | 10.0.1.0.0 |  | Add a partner in the delivery carrier
[delivery_dropoff_site](delivery_dropoff_site/) | 10.0.1.1.0 |  | Send goods to sites in which customers come pick up package
[delivery_multi_destination](delivery_multi_destination/) | 10.0.1.1.0 |  | Multiple destinations for the same delivery method
[delivery_price_by_category](delivery_price_by_category/) | 10.0.1.0.0 |  | Change delivery price based on product's category
[delivery_price_rule_untaxed](delivery_price_rule_untaxed/) | 10.0.1.0.0 |  | Add untaxed amount to variables for price delivery price rule
[sale_delivery_rate](sale_delivery_rate/) | 10.0.1.1.0 |  | Extends notion of delivery carrier rate quotes to sale orders
[stock_picking_delivery_info_computation](stock_picking_delivery_info_computation/) | 10.0.1.0.1 |  | Improve weight and volume calculation
[stock_picking_delivery_rate](stock_picking_delivery_rate/) | 10.0.1.0.0 |  | Adds a concept of rate quotes for stock pickings


Unported addons
---------------
addon | version | maintainers | summary
--- | --- | --- | ---
[delivery_carrier_file_laposte](delivery_carrier_file_laposte/) | 1.0 (unported) |  | Delivery Carrier File: La Poste
[delivery_carrier_label_default_webkit](delivery_carrier_label_default_webkit/) | 1.0 (unported) |  | Module for carrier labels
[delivery_carrier_label_dispatch](delivery_carrier_label_dispatch/) | 1.0 (unported) |  | Carrier labels - Picking dispatch (link)
[delivery_carrier_label_gls](delivery_carrier_label_gls/) | 0.1 (unported) |  | GLS carrier label printing
[delivery_carrier_label_postlogistics_shop_logo](delivery_carrier_label_postlogistics_shop_logo/) | 1.0 (unported) |  | PostLogistics labels - logo per Shop
[delivery_optional_invoice_line](delivery_optional_invoice_line/) | 0.1 (unported) |  | Delivery Optional Invoice Line

[//]: # (end addons)

Translation Status
------------------
[![Transifex Status](https://www.transifex.com/projects/p/OCA-carrier-delivery-10-0/chart/image_png)](https://www.transifex.com/projects/p/OCA-carrier-delivery-10-0)
