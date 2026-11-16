The shipping codes are generated when a stock picking which carrier is
configured for CTT Express Portugal as a provider is validated. The
shipping label is attached to the picking according to the configured
label format, and the carrier manifest (CA1) is attached after the
shipment is closed.

The first object code of the shipment is stored as the carrier tracking
reference and can be used in the CTT tracking page linked from the
picking.

Phone numbers are normalized before being sent: numbers without a
country prefix get the +351 prefix, duplicated numbers are sent only
once, and mobile numbers are sent in the MobilePhone field because CTT
rejects them in the Phone field.
