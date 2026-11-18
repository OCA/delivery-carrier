# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    is_strict_weight_package = fields.Boolean(
        string="Overweight package forbidden",
        help="The maximum weight of packages can't be exceeded.",
        compute="_compute_is_strict_weight_package",
        store=True,
        readonly=False,
    )

    @api.depends("company_id.delivery_carrier_strict_weight_package")
    def _compute_is_strict_weight_package(self):
        for rec in self:
            rec.is_strict_weight_package = (
                rec.company_id.delivery_carrier_strict_weight_package
                if rec.company_id
                else False
            )
