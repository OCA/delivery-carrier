This module needs the zeep python library, already required by Odoo.
It depends on the modules delivery_package_number and
delivery_price_method that can be found on OCA/delivery-carrier.

The following hosts should be visible from your Odoo deployment:

- Test: logistica.cttexpresso.pt:8082
- Production: cttexpressows.ctt.pt

For mobile numbers to be sent to CTT in the dedicated field, the OCA
``partner_mobile`` module (OCA/partner-contact) is recommended, as
Odoo 19 no longer provides ``res.partner.mobile`` natively.
