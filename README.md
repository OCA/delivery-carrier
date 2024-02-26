
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/delivery-carrier&target_branch=16.0)
[![Pre-commit Status](https://github.com/OCA/delivery-carrier/actions/workflows/pre-commit.yml/badge.svg?branch=16.0)](https://github.com/OCA/delivery-carrier/actions/workflows/pre-commit.yml?query=branch%3A16.0)
[![Build Status](https://github.com/OCA/delivery-carrier/actions/workflows/test.yml/badge.svg?branch=16.0)](https://github.com/OCA/delivery-carrier/actions/workflows/test.yml?query=branch%3A16.0)
[![codecov](https://codecov.io/gh/OCA/delivery-carrier/branch/16.0/graph/badge.svg)](https://codecov.io/gh/OCA/delivery-carrier)
[![Translation Status](https://translation.odoo-community.org/widgets/delivery-carrier-16-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/delivery-carrier-16-0/?utm_source=widget)

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
[base_delivery_carrier_label](base_delivery_carrier_label/) | 16.0.1.1.1 |  | Base module for carrier labels
[carrier_account_environment](carrier_account_environment/) | 16.0.1.0.0 | [![florian-dacosta](https://github.com/florian-dacosta.png?size=30px)](https://github.com/florian-dacosta) | Configure carriers with server_environment_files
[delivery_auto_refresh](delivery_auto_refresh/) | 16.0.1.0.1 |  | Auto-refresh delivery price in sales orders
[delivery_automatic_package](delivery_automatic_package/) | 16.0.1.0.0 |  | Allows to set a delivery package automatically when sending to shipper.
[delivery_carrier_account](delivery_carrier_account/) | 16.0.1.0.1 |  | Delivery Carrier Account
[delivery_carrier_agency](delivery_carrier_agency/) | 16.0.1.0.0 |  | Add a model for Carrier Agencies
[delivery_carrier_deposit](delivery_carrier_deposit/) | 16.0.1.0.0 |  | Create deposit slips
[delivery_carrier_info](delivery_carrier_info/) | 16.0.1.0.0 |  | Add code on carrier
[delivery_carrier_max_weight_constraint](delivery_carrier_max_weight_constraint/) | 16.0.1.0.1 |  | Constrain package maximum weight
[delivery_carrier_partner](delivery_carrier_partner/) | 16.0.1.0.0 |  | Add a partner in the delivery carrier
[delivery_cttexpress](delivery_cttexpress/) | 16.0.1.1.0 |  | Delivery Carrier implementation for CTT Express API
[delivery_deliverea](delivery_deliverea/) | 16.0.1.0.1 |  | Delivery Carrier implementation for Deliverea using their API
[delivery_driver](delivery_driver/) | 16.0.1.0.0 | [![EmilioPascual](https://github.com/EmilioPascual.png?size=30px)](https://github.com/EmilioPascual) [![rafaelbn](https://github.com/rafaelbn.png?size=30px)](https://github.com/rafaelbn) | Allow choose driver in delivery methods
[delivery_driver_stock_picking_batch](delivery_driver_stock_picking_batch/) | 16.0.1.0.1 | [![EmilioPascual](https://github.com/EmilioPascual.png?size=30px)](https://github.com/EmilioPascual) | Add drivers from delivery in stock picking batch
[delivery_estimated_package_quantity_by_weight](delivery_estimated_package_quantity_by_weight/) | 16.0.1.0.0 |  | Compute the amount of packages a picking out should have depending on the weight of the products and the limit fixed by the carrier
[delivery_package_fee](delivery_package_fee/) | 16.0.1.1.1 |  | Add fees on delivered packages on shipping methods
[delivery_package_number](delivery_package_number/) | 16.0.2.0.0 |  | Set or compute number of packages for a picking
[delivery_package_type_number_parcels](delivery_package_type_number_parcels/) | 16.0.1.0.1 |  | Number of parcels in a package type
[delivery_postlogistics](delivery_postlogistics/) | 16.0.1.0.4 |  | Print PostLogistics shipping labels using the Barcode web service
[delivery_postlogistics_server_env](delivery_postlogistics_server_env/) | 16.0.1.0.0 |  | Server Environment layer for Delivery Postlogistics
[delivery_price_method](delivery_price_method/) | 16.0.1.0.0 |  | Provides fields to be able to contemplate the tracking statesand also adds a global fields
[delivery_roulier](delivery_roulier/) | 16.0.1.0.0 | [![florian-dacosta](https://github.com/florian-dacosta.png?size=30px)](https://github.com/florian-dacosta) | Integration of multiple carriers
[delivery_state](delivery_state/) | 16.0.1.1.0 |  | Provides fields to be able to contemplate the tracking statesand also adds a global fields
[partner_delivery_schedule](partner_delivery_schedule/) | 16.0.1.0.0 |  | Set on partners a schedule for delivery goods
[partner_delivery_zone](partner_delivery_zone/) | 16.0.1.0.1 |  | This module allows to create partner delivery zones for physical products
[server_environment_delivery](server_environment_delivery/) | 16.0.1.0.0 |  | Configure prod environment for delivery carriers
[stock_picking_delivery_link](stock_picking_delivery_link/) | 16.0.1.1.0 |  | Adds link to the delivery on all intermediate operations.
[stock_picking_report_delivery_cost](stock_picking_report_delivery_cost/) | 16.0.1.0.0 |  | Show delivery cost in delivery slip and picking operations reports

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
