# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from .dachser_master_data import DACHSER_PACKAGING_CODES


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("dachser", "Dachser")],
        ondelete={"dachser": "set default"},
    )
    dachser_packaging_code = fields.Selection(
        selection=DACHSER_PACKAGING_CODES,
        string="Dachser Packaging Type",
        default="EU",
        help=(
            "Official package/pallet type code in the Dachser API "
            "(e.g. EU = Euro Pallet, EP = Dusseldorf Half Pallet, "
            "KT = Carton, PA = Pallet)."
        ),
    )
    dachser_stackable = fields.Boolean(
        string="Stackable (Dachser)",
        default=True,
        help="Indicates whether goods can be stacked on top of this package type.",
    )

    @api.onchange("package_carrier_type", "dachser_packaging_code")
    def _onchange_dachser_packaging_code(self):
        if self.package_carrier_type == "dachser" and self.dachser_packaging_code:
            self.shipper_package_code = self.dachser_packaging_code

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (
                vals.get("package_carrier_type") == "dachser"
                and vals.get("dachser_packaging_code")
                and not vals.get("shipper_package_code")
            ):
                vals["shipper_package_code"] = vals["dachser_packaging_code"]
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("dachser_packaging_code") and "shipper_package_code" not in vals:
            for rec in self:
                if (
                    vals.get("package_carrier_type") or rec.package_carrier_type
                ) == "dachser":
                    rec.shipper_package_code = vals["dachser_packaging_code"]
        return super().write(vals)
