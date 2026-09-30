This module extends the functionality of the delivery module to allow setting
delivery hours and days for partners.

It also provides a ``get_next_schedule()`` helper on ``delivery.schedule``
recordsets and on ``res.partner`` to compute the next reachable departure,
respecting weekday flags, timezone conversions and a configurable search
horizon set per company.
