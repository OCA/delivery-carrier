# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    available_delivery_schedule_ids = fields.Many2many(
        comodel_name="delivery.schedule",
        compute="_compute_available_delivery_schedule_ids",
        store=True,
        readonly=True,
        copy=False,
    )
    delivery_schedule_id = fields.Many2one(
        comodel_name="delivery.schedule",
        copy=False,
        help="Schedule time slot assigned to this order at confirmation.",
        domain="[('id', 'in', delivery_zone_id.delivery_schedule_ids.ids"
        " if delivery_zone_id else [])]",
    )
    scheduled_date = fields.Datetime(
        copy=False,
        help="Concrete departure date/time of the assigned schedule.",
    )
    cutoff_time = fields.Datetime(
        compute="_compute_cutoff_time",
        help="Last moment to confirm so the order makes its scheduled departure.",
    )

    @api.depends(
        "delivery_zone_id",
        "partner_shipping_id.delivery_zone_id",
        "partner_shipping_id.delivery_schedule_ids",
    )
    def _compute_available_delivery_schedule_ids(self):
        for order in self:
            partner = order.partner_shipping_id
            if partner.delivery_zone_id == order.delivery_zone_id:
                order.available_delivery_schedule_ids = partner.delivery_schedule_ids
            else:
                order.available_delivery_schedule_ids = (
                    order.delivery_zone_id.delivery_schedule_ids
                )

    @api.onchange("delivery_zone_id", "partner_shipping_id")
    def _onchange_delivery_zone_partner(self):
        self._compute_available_delivery_schedule_ids()
        if self.delivery_schedule_id not in self.available_delivery_schedule_ids:
            self.delivery_schedule_id = False

    @api.depends("scheduled_date")
    def _compute_cutoff_time(self):
        for order in self:
            minutes = order.company_id.delivery_cutoff_minutes
            order.cutoff_time = (
                order.scheduled_date - timedelta(minutes=minutes)
                if order.scheduled_date
                else False
            )

    def get_next_schedule(self, from_date=None, tz=None, horizon=None):
        """Return ``(schedule, departure)`` for the earliest reachable departure.

        A slot is reachable only when its departure is further away than the
        cutoff window, so an order placed too close to a departure rolls to the
        following one (possibly on the next active day).
        """
        self.ensure_one()
        empty_schedule = self.env["delivery.schedule"]
        zone = self.delivery_zone_id
        if not zone:
            return empty_schedule, False
        cutoff_minutes = self.company_id.delivery_cutoff_minutes
        if self.partner_id.delivery_schedule_ids:
            from_record = self.partner_id
        else:
            from_record = self.delivery_zone_id
        return from_record.get_next_schedule(
            from_date=fields.Datetime.now() + timedelta(minutes=cutoff_minutes),
            tz=tz,
            horizon=horizon,
        )

    def _assign_delivery_schedule(self, force=False):
        """Assign the next reachable departure slot.

        By default only orders without a slot are assigned. With ``force=True``
        every order is re-assigned, replacing any current (possibly overdue) slot.
        """
        orders = self if force else self.filtered(lambda o: not o.delivery_schedule_id)
        for order in orders:
            schedule, departure = order.get_next_schedule()
            if schedule:
                order.write(
                    {
                        "delivery_schedule_id": schedule.id,
                        "scheduled_date": departure,
                    }
                )

    def _action_confirm(self):
        """Assign a departure slot before the standard confirmation runs."""
        self._assign_delivery_schedule()
        return super()._action_confirm()
