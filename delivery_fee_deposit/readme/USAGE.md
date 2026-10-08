When this module is installed, delivery fees follow these rules:

- The sale order that creates the customer deposit applies the delivery fee.
- A delivery that only delivers products from the customer deposit does not apply
  the delivery fee.
- A mixed delivery, with products from the customer deposit and regular stock,
  applies the delivery fee normally.

**Behavior matrix**

| Scenario | Exempt | Delivery fee applied |
| --- | --- | --- |
| Sale creating a customer deposit | Yes | No |
| Sale creating a customer deposit | No | Yes |
| Delivery fully from customer deposit | Yes | No |
| Delivery fully from customer deposit | No | No |
| Mixed delivery: customer deposit + regular stock | Yes | No |
| Mixed delivery: customer deposit + regular stock | No | Yes |
| Delivery fully from pre-existing customer deposit | Yes | No |
| Delivery fully from pre-existing customer deposit | No | No |

A pre-existing customer deposit means customer-owned stock already available
before the sale being delivered. Releasing it should not create a new delivery
fee, even for successive deliveries.

**Return behavior matrix**

| Scenario | Return condition | Delivery fee reimbursed |
| --- | --- | --- |
| Sale creating a customer deposit | Deposit creation picking fully returned | Yes, per carrier config |
| Delivery fully from customer deposit | Returned | No fee existed |
| Mixed delivery: deposit + regular stock | Only deposit products returned | No |
| Mixed delivery: deposit + regular stock | All regular-stock products returned | Yes, per carrier config |
| Delivery fully from pre-existing customer deposit | Returned | No fee existed |

For mixed deliveries, the fee belongs to the regular-stock shipment. Returning
only the customer-deposit products must not reimburse it; returning all regular
products does.
