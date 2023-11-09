# Copyright 2020 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    number_of_packages = fields.Integer(
        string="Number of Packages",
        compute="_compute_number_of_packages",
        readonly=False,
        store=True,
        default=0,
        copy=False,
    )

    @api.depends("package_ids")
    def _compute_number_of_packages(self):
        for picking in self:
            if picking.package_ids:
                picking.number_of_packages = len(picking.package_ids)

    def _action_generate_number_of_packages_wizard(self):
        view = self.env.ref("delivery_package_number.view_number_package_validate")
        return {
            "name": _("Set number of packages"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "stock.number.package.validate.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "context": dict(
                self.env.context, default_pick_ids=[(4, p.id) for p in self]
            ),
        }

    def _check_set_number_of_packages(self):
        pickings_to_set_number_of_packages = self.browse()
        for picking in self:
            if (
                picking.picking_type_id.force_set_number_of_packages
                and not picking.number_of_packages
            ):
                pickings_to_set_number_of_packages |= picking
        return pickings_to_set_number_of_packages

    def _pre_action_done_hook(self):
        res = super()._pre_action_done_hook()
        if (
            res
            and isinstance(res, bool)
            and not self.env.context.get("bypass_set_number_of_packages")
        ):
            pickings_to_set_nop = self._check_set_number_of_packages()
            if pickings_to_set_nop:
                return pickings_to_set_nop._action_generate_number_of_packages_wizard()
        return res
