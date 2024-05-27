You have to set the created shipping method in the delivery order to ship:

* When the picking is 'Transferred', a *Create Shipping Label* button appears. Just
  click on it, and if all went well, the label will be 'attached'.
* If the shipment creation process fails, a validation error will appear displaying UPS
  error.
* When the delivery order is cancelled, it's automatically cancelled too in UPS.
* If you have "Tracking state update sync" checked in the shipping method, a periodical
  state check will be done querying UPS services.
