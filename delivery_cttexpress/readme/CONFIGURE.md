CTT Express Iberic Web Services API doesn't provide shipping price
calculation methods. So you'll have to rely on Odoo standard methods
selecting them in the field *Price method*.

To configure your CTT Express services, go to:

1.  *Inventory/Sales \> Configuration \> Delivery methods* and create a
    new one.
2.  Choose *CTT Express* as provider.
3.  Configure your CTT credentials: contract, agency, customer code,
    user and password.
4.  Configure your label format:
    - Single: Thermal printer (single label).
    - MULTI1: One label per sheet.
    - MULTI3: Protrait 3 labels per sheet.
    - MULTI4: Landscape 4 labels per sheet.
5.  You can also can configure your printer offset.
6.  Choose you shipping service.

If you wish to configure several services with the same credentials,
duplicate the first you made and change the service in the copy.
