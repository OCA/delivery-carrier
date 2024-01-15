# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    driver_id = fields.Many2one(
        "res.partner",
        "Default Driver",
        domain="[('is_company', '=', False)]",
        help="Default driver for this delivery method",
    )
