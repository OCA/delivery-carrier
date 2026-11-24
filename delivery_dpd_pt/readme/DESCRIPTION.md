[DPD Portugal](https://www.dpd.pt) is a leading parcel delivery service in Portugal,
offering express, standard, and economy delivery services with comprehensive
tracking and customer notification features.

This module integrates DPD Portugal shipping services with Odoo. It allows you to
send shipments, generate shipping labels, and follow parcels on the DPD
tracking portal directly from delivery orders.

It leverages the DPD Portugal REST API to register shipments and download
shipping labels automatically upon delivery order validation. The agreed
transport price configured on the carrier is used for shipping costs, as
the DPD API does not provide rating. Cash on delivery and DPD Predict
delivery are supported.

When the OCA `partner_mobile` module is installed, its mobile phone field is
used for the DPD mobile contact data. Without it, the regular partner phone
field is used as a fallback.
