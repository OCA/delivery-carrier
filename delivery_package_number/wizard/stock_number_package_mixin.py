# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockNumberPackageMixin(models.AbstractModel):
    _name = "stock.number.package.mixin"
    _description = "Mixin to set number of packages"

    number_of_packages = fields.Integer(
        help="Set the number of packages for this picking(s)",
    )
    ask_number_of_packages = fields.Boolean(compute="_compute_ask_number_of_packages")
    print_package_label = fields.Boolean(
        compute="_compute_print_package_label", readonly=False, store=True
    )

    @api.depends("pick_ids")
    def _compute_ask_number_of_packages(self):
        for item in self:
            # we use ._origin because if not, a NewId is used for the checks and the returned
            # value of package_ids is wrong.
            item.ask_number_of_packages = bool(
                item.pick_ids.carrier_id
                and not item.pick_ids._origin.package_ids
                or item.pick_ids.picking_type_id.force_set_number_of_packages
            )

    @api.depends("pick_ids")
    def _compute_print_package_label(self):
        for item in self:
            item.print_package_label = item.pick_ids.picking_type_id.print_label
