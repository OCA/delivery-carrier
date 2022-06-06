It allows to use other modules' external providers to create the delivery through webservice
  but not depend on them for rating the shipment. Instead we use the same table as the delivery
  type "Based on rules". This only applies if the Invoicing policy "Rule Cost" is used.

It supports the following use cases:

* When an external provider is used, a new option in the "Invoice Policy"
  selection, named "Rule Cost", overrides the provider's cost by the
  cost based on rules.
