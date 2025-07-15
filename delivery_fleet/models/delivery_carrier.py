# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle",
        help="Default Vehicle for this Carrier.",
    )
