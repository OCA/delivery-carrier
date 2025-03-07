# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    purchase_label_picking_type = fields.Many2one(
        string="Operation Type For Purchase Label", comodel_name="stock.picking.type"
    )
