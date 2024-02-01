# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    print_label_on_validate = fields.Boolean(
        string="Print label on validate",
        help="Print the number of packages label when validating a picking of this type",
    )
    force_set_number_of_packages = fields.Boolean()
    report_number_of_packages = fields.Many2one(
        "ir.actions.report",
        default=lambda self: self.env.ref(
            "delivery_package_number.action_delivery_package_number_report",
            raise_if_not_found=False,
        ),
    )
