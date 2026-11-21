- The module follows Bosta's public API documentation and is tested against mocked
  responses. It has not yet been validated against a live Bosta account.
- Cancelling from Odoo is not supported, because Bosta's public documentation does not
  show the path of its terminate endpoint. Cancel in the Bosta dashboard; the
  cancellation then arrives through the webhook.
- Rates use the delivery method's fixed price, since Bosta prices depend on each
  business's contract.
- Addresses send the state (governorate) or city and the street lines, without district
  or zone identifiers. The city must be a name Bosta recognises, such as Cairo, Giza, or
  Alexandria.
- Cash on delivery collects the remaining order total on an order's first shipment; later
  shipments of the same order collect nothing.
- Only standard deliveries (Bosta type 10) are created. Exchanges, customer returns, cash
  collection orders, and package dimensions are not covered.
- Bosta's webhook authentication is a static header without a signature, so a captured
  request could be replayed. Replays can only repeat a status or send an older one, which
  is ignored.
