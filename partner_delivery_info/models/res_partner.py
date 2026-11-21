# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    delivery_info_id = fields.Many2one(
        "res.partner.delivery.info",
        ondelete="restrict",
        string="Info for Delivery Carrier",
    )
