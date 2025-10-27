To configure this module, you need to:

1.  Add a Shipping Method with Provider ``CBL`` and introduce the User,
    Password, Client Code and Client Token.
2.  Choose the "Collect" "Freight Type" if the delivery needs to be paid by the receiver,
    or the "Prepaid" type if it needs to be paid by the shipper.
3.  Activate the "Cash On Delivery" option if shippings are paid by cash,
    assuming that the picking has a related sales order.
4.  Activate the "Needs Confirmation" option if shippings need to be
    confirmed after the tracking number is created in order to be oficially
    included in the CBL pending shippings database. It is crucial to have
    the same configuration both in Odoo and in your CBL account. Contact
    CBL for more information on how they can configure this feature.

**NOTE** Contact CBL to get testing credentials.
