
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/delivery-carrier&target_branch=12.0)
[![Pre-commit Status](https://github.com/OCA/delivery-carrier/actions/workflows/pre-commit.yml/badge.svg?branch=12.0)](https://github.com/OCA/delivery-carrier/actions/workflows/pre-commit.yml?query=branch%3A12.0)
[![Build Status](https://github.com/OCA/delivery-carrier/actions/workflows/test.yml/badge.svg?branch=12.0)](https://github.com/OCA/delivery-carrier/actions/workflows/test.yml?query=branch%3A12.0)
[![codecov](https://codecov.io/gh/OCA/delivery-carrier/branch/12.0/graph/badge.svg)](https://codecov.io/gh/OCA/delivery-carrier)
[![Translation Status](https://translation.odoo-community.org/widgets/delivery-carrier-12-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/delivery-carrier-12-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Carriers And Deliveries Management

This project aim to deal with modules related to manage carriers and deliveries in a generic way.

You'll find:

 - Generic module to generate file for carrier
 - Specific implementation for specific carrier (like la poste, tnt,..)
 - Generation of shipping labels for specific carrier (PostLogistics, ...)


<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[base_delivery_carrier_files](base_delivery_carrier_files/) | 12.0.1.0.1 |  | Base module for creation of delivery carrier files
[base_delivery_carrier_label](base_delivery_carrier_label/) | 12.0.3.4.0 |  | Base module for carrier labels
[delivery_auto_refresh](delivery_auto_refresh/) | 12.0.2.0.0 |  | Auto-refresh delivery price in sales orders
[delivery_carrier_info](delivery_carrier_info/) | 12.0.1.0.2 |  | Add code and description on carrier
[delivery_carrier_label_batch](delivery_carrier_label_batch/) | 12.0.1.0.2 |  | Carrier labels - Stock Batch Picking (link)
[delivery_carrier_label_default](delivery_carrier_label_default/) | 12.0.1.0.0 |  | This module defines a basic label to print when no specific carrier is selected.
[delivery_carrier_label_paazl](delivery_carrier_label_paazl/) | 12.0.1.3.0 |  | Print carrier labels for paazl
[delivery_carrier_label_postlogistics](delivery_carrier_label_postlogistics/) | 12.0.1.0.8 |  | Print postlogistics shipping labels
[delivery_carrier_label_ups](delivery_carrier_label_ups/) | 12.0.1.2.1 |  | Print carrier labels for ups
[delivery_carrier_partner](delivery_carrier_partner/) | 12.0.1.0.1 |  | Add a partner in the delivery carrier
[delivery_cttexpress](delivery_cttexpress/) | 12.0.1.0.0 |  | Delivery Carrier implementation for CTT Express API
[delivery_free_fee_removal](delivery_free_fee_removal/) | 12.0.1.0.0 |  | Remove free fee lines from sales order
[delivery_multi_destination](delivery_multi_destination/) | 12.0.1.1.0 |  | Multiple destinations for the same delivery method
[delivery_package_number](delivery_package_number/) | 12.0.1.0.0 |  | Set or compute number of packages for a picking
[delivery_price_method](delivery_price_method/) | 12.0.1.0.1 |  | Provides fields to be able to contemplate the tracking statesand also adds a global fields
[delivery_price_rule_untaxed](delivery_price_rule_untaxed/) | 12.0.1.0.2 |  | Add untaxed amount to variables for price delivery price rule
[delivery_state](delivery_state/) | 12.0.2.0.1 |  | Provides fields to be able to contemplate the tracking statesand also adds a global fields
[partner_delivery_schedule](partner_delivery_schedule/) | 12.0.1.2.0 |  | Set on partners a schedule for delivery goods
[partner_delivery_zone](partner_delivery_zone/) | 12.0.1.1.2 |  | Set on partners a zone for delivery goods
[stock_picking_delivery_info_computation](stock_picking_delivery_info_computation/) | 12.0.1.0.1 |  | Improve weight and volume calculation
[stock_picking_report_delivery_cost](stock_picking_report_delivery_cost/) | 12.0.1.0.0 |  | Show delivery cost in delivery slip and picking operations reports

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
