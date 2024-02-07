# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _name = "delivery.carrier"
    _inherit = ["delivery.carrier", "resource.mixin"]

    resource_id = fields.Many2one(
        string="Availability Resource",
        domain="[('resource_type', '=', 'carrier')]",
        required=False,
    )
