You have to set the created shipping method in the delivery order to
ship:

- When the picking is 'Transferred', a *Create Shipping Label* button
  appears. Just click on it, and if all went well, the label will be
  'attached'.
- If the shipment creation process fails, a validation error will appear
  displaying UPS error.
- When the delivery order is cancelled, it's automatically cancelled too
  in UPS.
- If you have "Tracking state update sync" checked in the shipping
  method, a periodical state check will be done querying UPS services.
- Each delivery order shows a *Declared Value*,
  pre-filled from the taxed price of the shipped products and the
  carrier's declared value percentage. You can adjust it manually before
  creating the label; when greater than zero it is sent to UPS as the
  package's declared value for insurance.
- For international shipments to countries configured in the
  "Automatically send paperless documents" field, the system will
  automatically prepare and send the required documentation to UPS when
  validating the picking. This includes:

  - Commercial Invoice: Automatically generated from the related sale
    order's invoice
  - Packing List: Automatically generated from the picking
  - Additional documents: You can manually attach other required
    documents (like certificates of origin, export licenses, etc.) to the
    picking using the "UPS Paperless Documents" tab

  If the sending fails, an error is displayed and the picking is not
  validated. You can also manually trigger the sending using the
  "Generate Paperless Documents" button on the picking form.

When UPS Global Checkout is configured and the destination is eligible:

- On rating an order (from the sales order or the eCommerce checkout), a
  separate "UPS Duties, Taxes & Fees" line is added below the
  shipping line.
