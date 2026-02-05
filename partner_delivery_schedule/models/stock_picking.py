# Copyright 2026 NICO SOLUTINS - ENGINEERING& IT (https://nnico-solutions.de).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    partner_delivery_schedule_warning = fields.Text(
        string="Delivery Schedule Warning",
        compute="_compute_partner_delivery_schedule_warning",
        store=True,
        readonly=True,
    )

    @api.depends("scheduled_date", "partner_id", "partner_id.delivery_schedule_ids")
    def _compute_partner_delivery_schedule_warning(self):
        for picking in self:
            picking.partner_delivery_schedule_warning = ""
            if not picking.partner_id or not picking.scheduled_date:
                continue

            dt_local = fields.Datetime.context_timestamp(
                picking, picking.scheduled_date
            )
            dt_naive = dt_local.replace(tzinfo=None)
            dt_str = fields.Datetime.to_string(dt_naive)

            if not picking.partner_id.allow_delivery_date(dt_str):
                formatted_delivery_date = dt_local.strftime("%m/%d/%Y %I:%M:%S %p")
                delivery_windows_strings = [
                    f"  * {s.display_name}"
                    for s in picking.partner_id.delivery_schedule_ids
                ]
                picking.partner_delivery_schedule_warning = self.env._(
                    "The scheduled delivery date is %(date)s, but the partner is "
                    "assigned to the following delivery schedule(s):\n%(windows)s",
                    date=formatted_delivery_date,
                    windows="\n".join(delivery_windows_strings)
                    if delivery_windows_strings
                    else "No delivery schedule defined",
                )
            else:
                picking.partner_delivery_schedule_warning = ""
