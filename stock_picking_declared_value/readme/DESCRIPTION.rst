This module extends the stock picking functionality to copy product prices from sales orders.
When a picking is created from a sales order, it copies the prices and discounts of each product line to the picking as declared values.
The purpose of this module is to serve other modules such as delivery carriers which require these
declared values when shipping a picking.

Additionally, the module allows configuring a "Declared Amount" on shipping methods (delivery carriers).
This percentage is used to calculate the final declared value for the picking. For example, if the total value
of products in a picking is $1000 and the declared amount is set to 80%, the declared value will be $800.

All declared value columns are hidden by default in the user interface but can be shown when needed.
