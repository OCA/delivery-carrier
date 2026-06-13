In some cases or industries, it is necessary to obtain a tracking reference before validating the picking.

For example, when a company sells products through an external marketplace that requires a tracking number for the delivery process even though the company has not yet shipped the products, as they might still be out of stock and require resupply from a vendor. 

The picking may be validated the next day or several days later, but a tracking number is still needed to report it to the marketplace.

NOTE: An alternative using the Odoo standard is to configure the warehouse with a two-step delivery process and, in the first picking type, mark the `Generate Shipping Labels` field so that, when validating the first picking, it is sent to the carrier and, in the second picking, the tracking reference is propagated from the first picking. However, when stock is not available, this feature does not work, which is the reason for this module.