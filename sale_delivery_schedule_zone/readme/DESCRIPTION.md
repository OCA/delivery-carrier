This module extends the OCA **partner_delivery_schedule_zone** module to
automatically assign a delivery schedule and departure date to sales orders
based on the partner's delivery zone.

When a sales order is confirmed, the next reachable departure slot is computed
from the partner's or zone's schedules, respecting a configurable cutoff window to avoid
assigning slots that are too close to the current time.
