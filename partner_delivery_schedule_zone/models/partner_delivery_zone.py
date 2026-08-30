# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class PartnerDeliveryZone(models.Model):
    _inherit = "partner.delivery.zone"

    delivery_schedule_ids = fields.Many2many(
        comodel_name="delivery.schedule",
        column1="delivery_zone_id",
        column2="delivery_schedule_id",
        relation="partner_delivery_zone_schedule_rel",
    )

    def get_next_schedule(self, from_date=None, tz=None, horizon=None):
        self.ensure_one()
        return self.delivery_schedule_ids.get_next_schedule(
            from_date=from_date, tz=tz, horizon=horizon
        )
