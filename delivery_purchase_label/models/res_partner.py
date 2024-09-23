# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"
    purchase_label_carrier_id = fields.Many2one(
        "delivery.carrier",
        string="Purchase Label Delivery Method",
        domain=[("purchase_label_picking_type", "!=", False)],
        help="Default carrier used for sending labels to the vendor",
    )
