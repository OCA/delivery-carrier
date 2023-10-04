Add delivery fees on Sales Orders based on the delivered packages.

A list of Package Fees can be added on shipping methods.
When a outgoing transfer is done, for each package fee configured on the
shipping method, a new sale order line is created with:

* The product selected on the Package Fee
* The product name with the number of the transfer in the line's description
  (e.g. "Service Fee (WH/OUT/00036)")
* The quantity equal to the number of packages in the transfer
* The unit price equal to the price set on the product's pricelist (so it can be
  different per customer and even have different pricing depending on the number
  of packages)
* The taxes configured on the product, fiscal position applies if any.

Package Fee lines are added only if their quantity and price is above zero.
