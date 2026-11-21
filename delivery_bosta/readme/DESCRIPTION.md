This module adds [Bosta](https://bosta.co), an Egyptian courier, as a delivery carrier.

- Validating a delivery order creates the delivery in Bosta and stores the tracking
  number on the transfer, with a link to Bosta's public tracking page.
- When the sales order was paid with Odoo's Cash on Delivery payment method, Bosta is
  asked to collect the order total. Prepaid orders are sent without a cash amount.
- Each delivery is created with this database's webhook URL and a secret
  Authorization value. Bosta then posts every state change, and the module records it
  in the tracking state, the tracking history, and the carrier state of
  `delivery_state` (in transit, incident, customer delivered, returned, canceled).
- Addresses are checked before anything is sent, and Bosta's own error message is
  shown when it rejects a delivery.
