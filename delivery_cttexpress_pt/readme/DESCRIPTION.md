CTT Express Portugal e-pool Web Services API integration with Odoo.

This module implements the *ShipmentProvider* SOAP API used by CTT
Expresso in Portugal. It is the Portugal counterpart of
``delivery_cttexpress``, which targets the Iberic/Tourline API used in
Spain: both are CTT services but they use different endpoints,
credentials and contracts, so they cannot be interchanged.

When a delivery order is validated, the module creates the shipment,
attaches the shipping label to the picking and closes the shipment to
obtain the carrier manifest (CA1) document.

The API does not provide shipment cancellation, tracking or pickup
scheduling operations, so those features are not implemented.
