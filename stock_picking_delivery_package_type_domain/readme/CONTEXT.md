In Odoo delivery module, you can choose the delivery package type if the carrier
is defined on the stock picking.

The filtered package types displayed are based on the package type package_carrier_type
field. That domain is set on the view and is not extendable.

This is why this module changed the domain in view to a computed field.
