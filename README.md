
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/delivery-carrier&target_branch=17.0)
[![Pre-commit Status](https://github.com/OCA/delivery-carrier/actions/workflows/pre-commit.yml/badge.svg?branch=17.0)](https://github.com/OCA/delivery-carrier/actions/workflows/pre-commit.yml?query=branch%3A17.0)
[![Build Status](https://github.com/OCA/delivery-carrier/actions/workflows/test.yml/badge.svg?branch=17.0)](https://github.com/OCA/delivery-carrier/actions/workflows/test.yml?query=branch%3A17.0)
[![codecov](https://codecov.io/gh/OCA/delivery-carrier/branch/17.0/graph/badge.svg)](https://codecov.io/gh/OCA/delivery-carrier)
[![Translation Status](https://translation.odoo-community.org/widgets/delivery-carrier-17-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/delivery-carrier-17-0/?utm_source=widget)

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
[base_delivery_carrier_label](base_delivery_carrier_label/) | 17.0.1.1.0 |  | Base module for carrier labels
[delivery_auto_refresh](delivery_auto_refresh/) | 17.0.1.0.0 |  | Auto-refresh delivery price in sales orders
[delivery_carrier_account](delivery_carrier_account/) | 17.0.1.0.0 |  | Delivery Carrier Account
[delivery_carrier_global_manifest](delivery_carrier_global_manifest/) | 17.0.1.0.0 | <a href='https://github.com/tisho99'><img src='https://github.com/tisho99.png' width='32' height='32' style='border-radius:50%;' alt='tisho99'/></a> | Manifest files for all carriers
[delivery_carrier_info](delivery_carrier_info/) | 17.0.1.0.0 |  | Add code on carrier
[delivery_carrier_manual_price](delivery_carrier_manual_price/) | 17.0.1.0.0 |  | Allow setting manual shipping cost in sale order.
[delivery_carrier_manual_weight](delivery_carrier_manual_weight/) | 17.0.1.0.0 |  | Allow setting weight and shipping weight in stock transfers manually based on carrier.
[delivery_carrier_multi_zip](delivery_carrier_multi_zip/) | 17.0.1.0.0 |  | Multiple ZIP intervals for the same delivery method
[delivery_carrier_partner](delivery_carrier_partner/) | 17.0.1.0.0 |  | Add a partner in the delivery carrier
[delivery_cbl](delivery_cbl/) | 17.0.1.0.0 |  | Integrate CBL webservice
[delivery_correos_express](delivery_correos_express/) | 17.0.1.0.0 |  | Delivery Carrier implementation for Correos Express using their API
[delivery_cttexpress](delivery_cttexpress/) | 17.0.1.0.1 |  | Delivery Carrier implementation for CTT Express API
[delivery_free_fee_removal](delivery_free_fee_removal/) | 17.0.1.0.0 |  | Hide free fee lines on sales orders
[delivery_multi_destination](delivery_multi_destination/) | 17.0.1.0.1 |  | Multiple destinations for the same delivery method
[delivery_package_number](delivery_package_number/) | 17.0.1.0.0 |  | Set or compute number of packages for a picking
[delivery_price_method](delivery_price_method/) | 17.0.1.0.0 |  | Force a fixed or rule price calculation on Delivery Methods, for example to override a webservice provided prices.
[delivery_purchase](delivery_purchase/) | 17.0.1.0.0 |  | Delivery costs in purchases
[delivery_purchase_multi_destination](delivery_purchase_multi_destination/) | 17.0.1.0.0 |  | Multiple origins for delivery costs in purchases
[delivery_roulier](delivery_roulier/) | 17.0.1.0.1 | <a href='https://github.com/florian-dacosta'><img src='https://github.com/florian-dacosta.png' width='32' height='32' style='border-radius:50%;' alt='florian-dacosta'/></a> | Integration of multiple carriers
[delivery_roulier_option](delivery_roulier_option/) | 17.0.1.0.0 | <a href='https://github.com/florian-dacosta'><img src='https://github.com/florian-dacosta.png' width='32' height='32' style='border-radius:50%;' alt='florian-dacosta'/></a> | Add options to roulier modules
[delivery_sendcloud_oca](delivery_sendcloud_oca/) | 17.0.1.0.0 |  | Compute shipping costs and ship with Sendcloud
[delivery_state](delivery_state/) | 17.0.1.0.0 |  | Provides fields to be able to contemplate the tracking statesand also adds a global fields
[delivery_ups_oca](delivery_ups_oca/) | 17.0.1.0.0 |  | Integrate UPS webservice
[partner_delivery_info](partner_delivery_info/) | 17.0.1.0.0 |  | Send delivery notice to the shipper from any operation.
[partner_delivery_schedule](partner_delivery_schedule/) | 17.0.1.0.0 |  | Set on partners a schedule for delivery goods
[partner_delivery_zone](partner_delivery_zone/) | 17.0.1.0.0 |  | Enables partner delivery zones for physical products
[sale_order_warehouse_from_delivery_carrier](sale_order_warehouse_from_delivery_carrier/) | 17.0.1.0.0 |  | Sale Order WH from Delivery Carrier

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
