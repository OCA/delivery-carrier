A delivery shipped in several parcels gets one tracking reference per parcel
from the carrier. Odoo keeps a single *Tracking Reference* on the transfer,
so today those deliveries are either split into one transfer per parcel,
which spoils the traceability of the order, or the references are typed as
one comma separated text nobody can search or report on.

This module puts the tracking reference on the package: the warehouse puts
the goods of each parcel in a package, types the reference of the parcel on
it, and the transfer shows the references of all its packages, as the carrier
integrations do when they ship several parcels. A carrier can require a
tracking reference on every package before the delivery is validated.
