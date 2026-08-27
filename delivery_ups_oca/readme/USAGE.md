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
- For international shipments to countries configured in the
  "Automatically send paperless invoice" field, the system will
  automatically prepare and send the required documentation to UPS when
  validating the picking. This includes:

  - Commercial Invoice: Automatically generated from the related sale
    order's invoice
  - Packing List: Automatically generated from the picking
  - Additional documents: You can manually attach other required
    documents (like certificates of origin, export licenses, etc.) to the
    picking using the "Paperless Document" tab

  If the automatic sending fails, a warning notification will be
  displayed, but the validation process will continue. You can also
  manually trigger the paperless invoice sending using the "Generate
  Paperless Invoice" button on the picking form.
