Turns Sendcloud returns into warehouse operations.

Customers request their return in the Sendcloud return portal: every portal
page offering the return slip of a Sendcloud delivery, such as the "Return"
button on the sales order portal, sends them there instead.
When the return reaches Odoo, this module resolves the original delivery, reads
the returned items from the incoming parcel and creates the matching return
operation, so the warehouse knows what is coming back and why before the parcel
arrives.

Returns created directly in Sendcloud are picked up the same way.
