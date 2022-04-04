
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/delivery-carrier&target_branch=14.0)
[![Build Status](https://travis-ci.com/OCA/delivery-carrier.svg?branch=14.0)](https://travis-ci.com/OCA/delivery-carrier)
[![codecov](https://codecov.io/gh/OCA/delivery-carrier/branch/14.0/graph/badge.svg)](https://codecov.io/gh/OCA/delivery-carrier)
[![Translation Status](https://translation.odoo-community.org/widgets/delivery-carrier-14-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/delivery-carrier-14-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# delivery-carrier

TODO: add repo description.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[base_delivery_carrier_files](base_delivery_carrier_files/) | 14.0.1.0.0 |  | Base module for creation of delivery carrier files
[base_delivery_carrier_label](base_delivery_carrier_label/) | 14.0.1.2.1 |  | Base module for carrier labels
[carrier_account_environment](carrier_account_environment/) | 14.0.1.0.1 | [![florian-dacosta](https://github.com/florian-dacosta.png?size=30px)](https://github.com/florian-dacosta) | Configure carriers with server_environment_files
[delivery_carrier_agency](delivery_carrier_agency/) | 14.0.1.0.1 |  | Add a model for Carrier Agencies
[delivery_carrier_category](delivery_carrier_category/) | 14.0.1.0.0 | [![rousseldenis](https://github.com/rousseldenis.png?size=30px)](https://github.com/rousseldenis) | Adds a category to delivery carriers in order to help users classifying them
[delivery_carrier_city](delivery_carrier_city/) | 14.0.1.0.0 | [![ivantodorovich](https://github.com/ivantodorovich.png?size=30px)](https://github.com/ivantodorovich) | Integrates delivery with base_address_city
[delivery_carrier_default_tracking_url](delivery_carrier_default_tracking_url/) | 14.0.1.0.0 | [![rousseldenis](https://github.com/rousseldenis.png?size=30px)](https://github.com/rousseldenis) | Adds the default tracking url on delivery carrier
[delivery_carrier_info](delivery_carrier_info/) | 14.0.1.0.1 |  | Add code and description on carrier
[delivery_carrier_label_batch](delivery_carrier_label_batch/) | 14.0.1.0.0 |  | Carrier labels - Stock Batch Picking (link)
[delivery_carrier_location](delivery_carrier_location/) | 14.0.1.0.0 | [![ivantodorovich](https://github.com/ivantodorovich.png?size=30px)](https://github.com/ivantodorovich) | Integrates delivery with base_location
[delivery_carrier_partner](delivery_carrier_partner/) | 14.0.1.0.0 |  | Add a partner in the delivery carrier
[delivery_carrier_pricelist](delivery_carrier_pricelist/) | 14.0.1.0.1 |  | Compute method method fees based on the product's pricelist.
[delivery_correos_express](delivery_correos_express/) | 14.0.1.0.0 |  | Delivery Carrier implementation for Correos Express using their API
[delivery_free_fee_removal](delivery_free_fee_removal/) | 14.0.1.0.0 |  | Hide free fee lines on sales orders
[delivery_multi_destination](delivery_multi_destination/) | 14.0.1.0.1 |  | Multiple destinations for the same delivery method
[delivery_package_fee](delivery_package_fee/) | 14.0.1.0.2 |  | Add fees on delivered packages on shipping methods
[delivery_package_number](delivery_package_number/) | 14.0.1.0.0 |  | Set or compute number of packages for a picking
[delivery_postlogistics](delivery_postlogistics/) | 14.0.1.0.1 |  | Print PostLogistics shipping labels using the Barcode web service
[delivery_postlogistics_server_env](delivery_postlogistics_server_env/) | 14.0.1.0.0 |  | Server Environment layer for Delivery Postlogistics
[delivery_roulier](delivery_roulier/) | 14.0.1.0.1 | [![florian-dacosta](https://github.com/florian-dacosta.png?size=30px)](https://github.com/florian-dacosta) | Integration of multiple carriers
[delivery_roulier_laposte_fr](delivery_roulier_laposte_fr/) | 14.0.1.0.1 | [![florian-dacosta](https://github.com/florian-dacosta.png?size=30px)](https://github.com/florian-dacosta) | Generate Label for La Poste/Colissimo
[delivery_roulier_option](delivery_roulier_option/) | 14.0.1.0.0 | [![florian-dacosta](https://github.com/florian-dacosta.png?size=30px)](https://github.com/florian-dacosta) | Add options to roulier modules
[delivery_schenker](delivery_schenker/) | 14.0.1.0.0 |  | Delivery Carrier implementation for DB Schenker API
[delivery_send_to_shipper_at_operation](delivery_send_to_shipper_at_operation/) | 14.0.1.0.0 |  | Send delivery notice to the shipper from any operation.
[delivery_state](delivery_state/) | 14.0.1.0.0 |  | Provides fields to be able to contemplate the tracking statesand also adds a global fields
[partner_default_delivery_carrier](partner_default_delivery_carrier/) | 14.0.1.0.0 | [![SilvioC2C](https://github.com/SilvioC2C.png?size=30px)](https://github.com/SilvioC2C) | Allows defining default delivery methods for partners
[partner_delivery_zone](partner_delivery_zone/) | 14.0.1.1.0 |  | Set on partners a zone for delivery goods
[server_environment_delivery](server_environment_delivery/) | 14.0.1.0.0 |  | Configure prod environment for delivery carriers
[stock_picking_carrier_from_rule](stock_picking_carrier_from_rule/) | 14.0.1.0.0 |  | Set the carrier on picking if the stock rule used has a partner address set with a delivery method.
[stock_picking_delivery_link](stock_picking_delivery_link/) | 14.0.1.0.0 |  | Adds link to the delivery on all intermediate operations.

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
