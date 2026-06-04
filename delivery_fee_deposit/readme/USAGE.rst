When this module is installed, delivery fees follow these rules:

* The sale order that creates the customer deposit applies the delivery fee.
* A delivery that only delivers products from the customer deposit does not apply
  the delivery fee.
* A mixed delivery, with products from the customer deposit and regular stock,
  applies the delivery fee normally.

Customer deposit deliveries are detected from the sale line route: if all stock
moves in the picking come from sale lines using the warehouse customer deposit
route, the picking is considered a full customer deposit delivery.
