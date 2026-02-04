To configure your Dachser services, go to:

1.  *Inventory/Sales \> Configuration \> Delivery methods* and create a
    new one.
2.  Choose *Dachser* as provider.
3.  Configure your Ddachser data: API key, Division Code, Product Code,
    Term Code, Packaging Code and Packaging Type

The API key is a piece of information that you will obtain when you
register at <https://api-portal.dachser.com/bi.b2b.portal/api/library>
and request access to the following APIs: - transportorder: To create
and cancel shipments. - shipmentstatus: To obtain the status of
shipments. - quotations: To obtain a quote for a shipment.

It is not possible to test transportorder with an API in test mode.

There is no such thing as a test and production environment at Dachser,
so changing the environment in the carrier's corresponding smart button
will have no implications.
