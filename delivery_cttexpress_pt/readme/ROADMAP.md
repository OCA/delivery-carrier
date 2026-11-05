**Status:** draft

## Decisions

- Implemented on top of zeep instead of raw XML envelopes: the WSDL is
  self-contained and zeep serializes the WCF DataContracts correctly,
  including the strict element ordering the service requires.
- Credentials live on the delivery carrier (production and optional
  test sets), following ``delivery_cttexpress``.
- The carrier *Test mode/Production mode* toggle selects the endpoint
  and credential set. There is no silent fallback to production.
- No tracking, cancel, pickup or manifest-report features: the
  ShipmentProvider API only exposes CreateShipment,
  CreateShipmentWithoutPrint, CompleteShipment and CloseShipment.
  Rejected: proxying those features through undocumented endpoints.
- ``partner_mobile`` is not a hard dependency: the module reads
  ``mobile`` with a ``getattr`` fallback so it also works without it.

## Tasks

- [ ] Validate against the CTT QA environment once it is reachable.
- [ ] Check whether CompleteShipment is needed in the shipment flow.
