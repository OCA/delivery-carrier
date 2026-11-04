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
