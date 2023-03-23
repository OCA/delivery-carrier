* After confirming the sales order, the price of the delivery line (if exists)
  will be only updated after the picking is transferred, but not when you
  might modify the order lines.
* There can be some duplicate delivery unset/set for assuring that the refresh
  is done on all cases.
* On multiple deliveries, second and successive pickings update the delivery
  price, but you can't invoice the new delivery price.
* This is only working from user interface, as there's no way of making
  compatible the auto-refresh intercepting create/write methods from sale order
  lines.
