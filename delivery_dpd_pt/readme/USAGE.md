1.  Create a sales order and select the DPD Portugal delivery method.
2.  Optionally set a **COD Amount** on the picking to ship with cash on
    delivery (amount must be in euros).
3.  Confirm the sales order and validate the delivery order.
4.  Click **Send to Shipper** to:
    - Register the shipment on the DPD Portugal API
    - Download and attach the shipping label
    - Set the guide number(s) as the tracking reference
5.  In production, use the tracking link on the delivery order to follow
    the parcel on the DPD tracking portal. The DPD API does not provide
    shipment status updates, so the tracking state is not updated
    automatically.

Labels are attached to the delivery order as soon as the shipment is
registered.
