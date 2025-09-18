
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/delivery-carrier&target_branch=18.0)
[![Pre-commit Status](https://github.com/OCA/delivery-carrier/actions/workflows/pre-commit.yml/badge.svg?branch=18.0)](https://github.com/OCA/delivery-carrier/actions/workflows/pre-commit.yml?query=branch%3A18.0)
[![Build Status](https://github.com/OCA/delivery-carrier/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/OCA/delivery-carrier/actions/workflows/test.yml?query=branch%3A18.0)
[![codecov](https://codecov.io/gh/OCA/delivery-carrier/branch/18.0/graph/badge.svg)](https://codecov.io/gh/OCA/delivery-carrier)
[![Translation Status](https://translation.odoo-community.org/widgets/delivery-carrier-18-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/delivery-carrier-18-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Delivery Carrier

Are you looking for modules related to logistics? Or would like to contribute
to? There are many repositories with specific purposes. Have a look at this
[README](https://github.com/OCA/wms/blob/18.0/README.md).

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[delivery_auto_refresh](delivery_auto_refresh/) | 18.0.1.0.0 |  | Auto-refresh delivery price in sales orders
[delivery_carrier_account](delivery_carrier_account/) | 18.0.1.0.0 |  | Delivery Carrier Account
[delivery_carrier_agency](delivery_carrier_agency/) | 18.0.1.0.0 |  | Add a model for Carrier Agencies
[delivery_carrier_info](delivery_carrier_info/) | 18.0.1.0.0 |  | Add code on carrier
[delivery_carrier_label_default](delivery_carrier_label_default/) | 18.0.1.0.0 |  | This module defines a basic label to print when no specific carrier is selected.
[delivery_carrier_manual_price](delivery_carrier_manual_price/) | 18.0.1.0.0 |  | Allow setting manual shipping cost in sale order.
[delivery_carrier_manual_weight](delivery_carrier_manual_weight/) | 18.0.1.0.0 |  | Allow setting weight and shipping weight in stock transfers manually based on carrier.
[delivery_carrier_max_weight_constraint](delivery_carrier_max_weight_constraint/) | 18.0.1.0.0 |  | Constrain package maximum weight
[delivery_carrier_option](delivery_carrier_option/) | 18.0.1.0.0 | <a href='https://github.com/florian-dacosta'><img src='https://github.com/florian-dacosta.png' width='32' height='32' style='border-radius:50%;' alt='florian-dacosta'/></a> | Delivery Carrier Option
[delivery_carrier_partner](delivery_carrier_partner/) | 18.0.1.0.0 |  | Add a partner in the delivery carrier
[delivery_carrier_picking_valid](delivery_carrier_picking_valid/) | 18.0.1.0.0 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> | Checks if a transfer matches carrier requirements
[delivery_carrier_picking_valid_dangerous_goods](delivery_carrier_picking_valid_dangerous_goods/) | 18.0.1.0.0 | <a href='https://github.com/mmequignon'><img src='https://github.com/mmequignon.png' width='32' height='32' style='border-radius:50%;' alt='mmequignon'/></a> | Checks if a transfer matches carrier dangerous goods restrictions
[delivery_carrier_pricelist](delivery_carrier_pricelist/) | 18.0.1.0.0 |  | Compute delivery method price based on the product's pricelist.
[delivery_carrier_shipping_label](delivery_carrier_shipping_label/) | 18.0.1.0.0 | <a href='https://github.com/florian-dacosta'><img src='https://github.com/florian-dacosta.png' width='32' height='32' style='border-radius:50%;' alt='florian-dacosta'/></a> | Delivery Carrier Shipping Label
[delivery_carrier_warehouse](delivery_carrier_warehouse/) | 18.0.1.0.1 |  | Get delivery method used in sales orders from warehouse
[delivery_driver](delivery_driver/) | 18.0.1.0.1 | <a href='https://github.com/EmilioPascual'><img src='https://github.com/EmilioPascual.png' width='32' height='32' style='border-radius:50%;' alt='EmilioPascual'/></a> <a href='https://github.com/rafaelbn'><img src='https://github.com/rafaelbn.png' width='32' height='32' style='border-radius:50%;' alt='rafaelbn'/></a> | Allow choose driver in delivery methods
[delivery_driver_stock_picking_batch](delivery_driver_stock_picking_batch/) | 18.0.1.0.1 | <a href='https://github.com/EmilioPascual'><img src='https://github.com/EmilioPascual.png' width='32' height='32' style='border-radius:50%;' alt='EmilioPascual'/></a> | Add drivers from delivery in stock picking batch
[delivery_dropoff_site](delivery_dropoff_site/) | 18.0.1.0.0 |  | Send goods to sites in which customers come pick up package
[delivery_free_fee_removal](delivery_free_fee_removal/) | 18.0.1.0.0 |  | Hide free fee lines on sales orders
[delivery_package_fee](delivery_package_fee/) | 18.0.1.0.0 |  | Add fees on sales order for delivered packages
[delivery_package_number](delivery_package_number/) | 18.0.1.0.0 |  | Set or compute number of packages for a picking
[delivery_package_type_number_parcels](delivery_package_type_number_parcels/) | 18.0.1.0.0 |  | Number of parcels in a package type
[delivery_package_type_shipping_weight](delivery_package_type_shipping_weight/) | 18.0.1.0.0 |  | Set and manage shipping weight based on package type.
[delivery_postlogistics](delivery_postlogistics/) | 18.0.1.2.1 |  | Print PostLogistics shipping labels using the Barcode web service
[delivery_postlogistics_dangerous_goods](delivery_postlogistics_dangerous_goods/) | 18.0.1.0.0 |  | Declare dangerous goods when generating postlogistics labels
[delivery_postlogistics_server_env](delivery_postlogistics_server_env/) | 18.0.1.0.0 |  | Server Environment layer for Delivery Postlogistics
[delivery_price_method](delivery_price_method/) | 18.0.1.0.0 |  | Force a fixed or rule price calculation on Delivery Methods, for example to override a webservice provided prices.
[delivery_roulier](delivery_roulier/) | 18.0.1.0.0 | <a href='https://github.com/florian-dacosta'><img src='https://github.com/florian-dacosta.png' width='32' height='32' style='border-radius:50%;' alt='florian-dacosta'/></a> <a href='https://github.com/hparfr'><img src='https://github.com/hparfr.png' width='32' height='32' style='border-radius:50%;' alt='hparfr'/></a> | Integration of multiple carriers
[delivery_state](delivery_state/) | 18.0.1.0.0 |  | Provides fields to be able to contemplate the tracking statesand also adds a global fields
[partner_delivery_info](partner_delivery_info/) | 18.0.1.0.0 |  | Send delivery notice to the shipper from any operation.
[partner_delivery_schedule](partner_delivery_schedule/) | 18.0.1.0.1 |  | Set on partners a schedule for delivery goods
[partner_delivery_zone](partner_delivery_zone/) | 18.0.1.0.0 |  | Enables partner delivery zones for physical products
[server_environment_delivery](server_environment_delivery/) | 18.0.1.0.0 |  | Configure prod environment for delivery carriers
[stock_fleet_delivery_driver](stock_fleet_delivery_driver/) | 18.0.1.0.1 | <a href='https://github.com/Shide'><img src='https://github.com/Shide.png' width='32' height='32' style='border-radius:50%;' alt='Shide'/></a> <a href='https://github.com/rafaelbn'><img src='https://github.com/rafaelbn.png' width='32' height='32' style='border-radius:50%;' alt='rafaelbn'/></a> <a href='https://github.com/EmilioPascual'><img src='https://github.com/EmilioPascual.png' width='32' height='32' style='border-radius:50%;' alt='EmilioPascual'/></a> | Allow choose Vehicle in Carriers, Transfers and Batches
[stock_picking_carrier_from_rule](stock_picking_carrier_from_rule/) | 18.0.1.0.0 |  | Set the carrier on picking if the stock rule used has a partner address set with a delivery method.
[stock_picking_delivery_link](stock_picking_delivery_link/) | 18.0.1.0.1 |  | Adds link to the delivery on all intermediate operations.
[stock_picking_delivery_package_type_domain](stock_picking_delivery_package_type_domain/) | 18.0.1.0.0 |  | This module will allow to extend the domain to filter package type selection in 'Choose Delivery Package' wizard
[stock_picking_report_delivery_cost](stock_picking_report_delivery_cost/) | 18.0.1.0.0 |  | Show delivery cost in delivery slip and picking operations reports

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
