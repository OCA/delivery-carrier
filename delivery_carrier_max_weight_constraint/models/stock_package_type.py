# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PackageType(models.Model):
    _inherit = "stock.package.type"

    is_strict_weight = fields.Boolean(
        string="Overweight forbidden",
        help="The maximum weight of the package can't be exceeded.",
        compute="_compute_is_strict_weight",
        store=True,
        readonly=False,
    )

    @api.depends("company_id.delivery_carrier_strict_weight_package")
    def _compute_is_strict_weight(self):
        for rec in self:
            rec.is_strict_weight = (
                rec.company_id.delivery_carrier_strict_weight_package
                if rec.company_id
                else False
            )
