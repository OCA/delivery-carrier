
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/delivery-carrier&target_branch=19.0)
[![Pre-commit Status](https://github.com/OCA/delivery-carrier/actions/workflows/pre-commit.yml/badge.svg?branch=19.0)](https://github.com/OCA/delivery-carrier/actions/workflows/pre-commit.yml?query=branch%3A19.0)
[![Build Status](https://github.com/OCA/delivery-carrier/actions/workflows/test.yml/badge.svg?branch=19.0)](https://github.com/OCA/delivery-carrier/actions/workflows/test.yml?query=branch%3A19.0)
[![codecov](https://codecov.io/gh/OCA/delivery-carrier/branch/19.0/graph/badge.svg)](https://codecov.io/gh/OCA/delivery-carrier)
[![Translation Status](https://translation.odoo-community.org/widgets/delivery-carrier-19-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/delivery-carrier-19-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# delivery-carrier

delivery-carrier

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[delivery_auto_refresh](delivery_auto_refresh/) | 19.0.1.0.0 |  | Auto-refresh delivery price in sales orders
[delivery_carrier_account](delivery_carrier_account/) | 19.0.1.0.0 |  | Delivery Carrier Account
[delivery_carrier_agency](delivery_carrier_agency/) | 19.0.1.0.0 |  | Add a model for Carrier Agencies
[delivery_carrier_info](delivery_carrier_info/) | 19.0.1.0.0 |  | Add code on carrier
[delivery_carrier_manual_price](delivery_carrier_manual_price/) | 19.0.1.0.0 |  | Allow setting manual shipping cost in sale order.
[delivery_carrier_multi_zip](delivery_carrier_multi_zip/) | 19.0.1.0.0 |  | Multiple ZIP intervals for the same delivery method
[delivery_carrier_option](delivery_carrier_option/) | 19.0.1.0.0 | <a href='https://github.com/florian-dacosta'><img src='https://github.com/florian-dacosta.png' width='32' height='32' style='border-radius:50%;' alt='florian-dacosta'/></a> | Delivery Carrier Option
[delivery_carrier_partner](delivery_carrier_partner/) | 19.0.1.0.0 |  | Add a partner in the delivery carrier
[delivery_carrier_picking_valid](delivery_carrier_picking_valid/) | 19.0.1.0.0 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> | Checks if a transfer matches carrier requirements
[delivery_carrier_picking_valid_dangerous_goods](delivery_carrier_picking_valid_dangerous_goods/) | 19.0.1.0.1 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> | Checks if a transfer matches carrier dangerous goods restrictions
[delivery_correos_express](delivery_correos_express/) | 19.0.1.0.0 |  | Delivery Carrier implementation for Correos Express using their API
[delivery_driver](delivery_driver/) | 19.0.1.0.0 | <a href='https://github.com/EmilioPascual'><img src='https://github.com/EmilioPascual.png' width='32' height='32' style='border-radius:50%;' alt='EmilioPascual'/></a> <a href='https://github.com/rafaelbn'><img src='https://github.com/rafaelbn.png' width='32' height='32' style='border-radius:50%;' alt='rafaelbn'/></a> | Allow choose driver in delivery methods
[delivery_driver_stock_picking_batch](delivery_driver_stock_picking_batch/) | 19.0.1.0.0 | <a href='https://github.com/EmilioPascual'><img src='https://github.com/EmilioPascual.png' width='32' height='32' style='border-radius:50%;' alt='EmilioPascual'/></a> | Add drivers from delivery in stock picking batch
[delivery_multi_destination](delivery_multi_destination/) | 19.0.1.0.1 |  | Multiple destinations for the same delivery method
[delivery_package_number](delivery_package_number/) | 19.0.1.0.0 |  | Set or compute number of packages for a picking
[delivery_price_method](delivery_price_method/) | 19.0.1.0.0 |  | Force a fixed or rule price calculation on Delivery Methods, for example to override a webservice provided prices.
[delivery_purchase](delivery_purchase/) | 19.0.1.0.2 |  | Delivery costs in purchases
[delivery_purchase_multi_destination](delivery_purchase_multi_destination/) | 19.0.1.0.0 |  | Multiple origins for delivery costs in purchases
[delivery_state](delivery_state/) | 19.0.1.1.0 |  | Provides fields to be able to contemplate the tracking statesand also adds a global fields
[partner_delivery_info](partner_delivery_info/) | 19.0.1.0.0 |  | Send delivery notice to the shipper from any operation.
[partner_delivery_schedule](partner_delivery_schedule/) | 19.0.1.0.0 |  | Set on partners a schedule for delivery goods
[partner_delivery_zone](partner_delivery_zone/) | 19.0.1.0.0 |  | Enables partner delivery zones for physical products
[partner_delivery_zone_calendar](partner_delivery_zone_calendar/) | 19.0.1.0.0 |  | This module allows to define a calendar on a delivery zone

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
