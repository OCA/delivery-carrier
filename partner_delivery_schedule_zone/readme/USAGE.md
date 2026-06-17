To use this module you need to:

1.  Install it together with **partner_delivery_schedule** so that delivery
    zones and delivery schedules are both available.
2.  Go to *Inventory \> Configuration \> Delivery Zones*.
3.  On a delivery zone, fill in the *Delivery Schedules* field with the delivery
    schedules reachable from that zone.

The `find_next_schedule` method can then be called on a
`partner.delivery.zone` record to retrieve the next reachable departure
(schedule and departure datetime).
