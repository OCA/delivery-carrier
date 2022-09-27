This module needs the `zeep` python library. It depends on the modules
`delivery_package_number` and `delivery_state` that can be found on
OCA/delivery-carrier.

CTT Express Iberic Web Services API doesn't provide shipping price calculation methods.
To rely on Odoo standard price calculations you'll to install the module
`delivery_price_method` found in this repository as well.

The following ports and hosts should be visible from your Odoo deployment:

- Test: iberws.tourlineexpress.com:8686
- Production: iberws.tourlineexpress.com:8700
