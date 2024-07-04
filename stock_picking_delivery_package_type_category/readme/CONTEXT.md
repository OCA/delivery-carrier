BUSINESS NEED: 

- Users doing the delivery are often different ones as users doing the picking.
- Delivery pickings would be able to know what kind of packages they will be able
  to manipulate. This concept was introduced in stock_package_type_category module.
- As delivery packages will be categorized, but maybe using the same carrier specifications,
  we need to filter package types by category in put in pack operation.

APPROACH:

- 'Authorized' package type categories will be set on the operation types (typically picking or packing ones).
