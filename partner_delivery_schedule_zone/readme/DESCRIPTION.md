This module extends the OCA **partner_delivery_zone** module to link delivery
zones with multiple delivery schedules.

It adds a `delivery_schedule_ids` field on `partner.delivery.zone` pointing to
`delivery.schedule`, and provides a `find_next_schedule` helper that computes
the next reachable departure for a zone, respecting weekday flags, timezone
conversions and a configurable search horizon (thanks to `partner_delivery_schedule`).
