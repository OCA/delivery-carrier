This module provides granular control over which service products impact the calculated expected delivery date on a Sales Order.

It works by directly filtering out the lead times from specific service lines before the final delivery date is determined.

1.  New Field: A boolean field named "Affect Delivery Date" is added to the product template ("Sales" tab, "Extra Info" section). It is visible only for products of type `service`.
2.  **Exclusion:** When a Sale Order line contains a Service Product where the "Affect Delivery Date" flag is unchecked:
    * The line's lead time is ignored.
    * This ensures the service product's delay is completely excluded from the final order date calculation.
3.  **Inclusion:** All other products (Physical Goods, and Services with the flag checked) contribute their standard lead time to the final delivery date.