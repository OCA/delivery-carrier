Print delivery labels for dropshipping purchase order.
Useful when the vendor that will process the order does not have the
capabilities to print the transporter labels needed for the delivery.

This is done by creating and processing a stock transfer with the source
and destination location set as the vendor location. And the carrier set.

The transporter being used is the one set on the `Purchase Delivery Method` of the
vendor in the "Sales & Purchase" tab.

A new operation type is created by the module and used for the transfer.
All attachment (should be only the labels) on the transfer are then attached
to the email send to the vendor (rfq or po).
When the purchase order is still in draft the labels are regenerated everytime
the email is sent.
