# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class DeliverySchedule(models.Model):
    _inherit = "delivery.schedule"

    delivery_zone_ids = fields.Many2many(
        comodel_name="partner.delivery.zone",
        column1="delivery_schedule_id",
        column2="delivery_zone_id",
        relation="partner_delivery_zone_schedule_rel",
    )
