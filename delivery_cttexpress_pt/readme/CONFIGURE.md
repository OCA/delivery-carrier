The CTT Express Portugal API doesn't provide shipping price
calculation methods. So you'll have to rely on Odoo standard methods
selecting them in the field *Price method* (the module defaults it to
*Based on Rules*).

To configure your CTT Express Portugal account, go to:

1.  *Inventory/Sales \> Configuration \> Delivery methods* and create a
    new one.
2.  Choose *CTT Express Portugal* as provider.
3.  In the *CTT Express Portugal* page, configure your e-pool
    credentials: authentication ID, client ID, contract ID,
    distribution channel ID and user ID.
4.  Optionally configure the *Test environment* credentials. Empty
    fields fall back to the production values. The carrier *Test
    mode/Production mode* toggle (Environment field) selects which
    endpoint and credentials are used for shipments.
5.  Choose the *Sub product* (Para amanhã, Em 2 dias or 19 Múltiplo),
    the label format (PDF or ZPL), whether sender information is
    printed on the label, and the export type and UPU code.

You can check the connectivity and credentials of each configured
endpoint with the *Test connection* button. It performs a harmless
close-shipment probe because the API has no ping operation.
