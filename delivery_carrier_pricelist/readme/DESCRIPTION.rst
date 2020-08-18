Compute shipping methods fees based on Product Pricelists.

It allows to have different pricing per customer, prices depending on dates, ...
The pricelist based cost is computed from the shipping method's product and the
sales order's pricelist.

It supports the following use cases:

* When no "external" provider (e.g. DHL, UPS, ...) is used, a new provider
  "Based on Product Pricelist" is available.
* When an external provider is used, a new option in the "Invoice Policy"
  selection, named "Pricelist Cost", overrides the provider's cost by the
  pricelist based cost.
