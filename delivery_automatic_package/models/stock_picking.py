# Copyright 2019 Akretion <https://www.akretion.com>.
# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _auto_create_delivery_package(self) -> None:
        if self.carrier_id.automatic_package_creation_mode == "packaging":
            self._auto_create_delivery_package_per_smallest_packaging()
        else:
            self._set_a_default_package()

    def _auto_create_delivery_package_per_smallest_packaging(self) -> None:
        """
        Put each done smallest product packaging in a package
        """
        for picking in self:
            for move_line in picking.move_line_ids:
                if not move_line.qty_done:
                    continue
                if move_line.result_package_id:
                    continue
                packagings = move_line.product_id.packaging_ids
                if not packagings:
                    raise UserError(
                        _(
                            "Cannot create a package for the product %s as "
                            "no product packaging is defined"
                        )
                        % move_line.product_id.display_name
                    )
                smallest_packaging = packagings.sorted("qty")[0]
                precision_digits = self.env["decimal.precision"].precision_get(
                    "Product Unit of Measure"
                )
                qty_done = move_line.qty_done
                qty = float_round(
                    qty_done / smallest_packaging.qty,
                    precision_digits=precision_digits,
                    rounding_method="HALF-UP",
                )
                if not qty.is_integer():
                    raise UserError(
                        _(
                            "The done quantity of the product %s is not "
                            "a multiple of product packaging"
                        )
                        % move_line.product_id.display_name
                    )
                for _i in range(int(qty)):
                    move_line.qty_done = smallest_packaging.qty
                    move_line.picking_id._put_in_pack(move_line)

    def _set_a_default_package(self) -> None:
        """
        For every move that don't have a package, set a new one.
        """
        for picking in self:
            move_lines = picking.move_line_ids.filtered(
                lambda s: not s.result_package_id
            )
            if move_lines:
                picking._put_in_pack(move_lines)

    def send_to_shipper(self) -> None:
        """
        If the automatic package creation is enabled (through configuration or context),
        set a new one for concerned moves.
        """
        self.ensure_one()
        if (
            self.carrier_id.automatic_package_creation_at_delivery
            or self.env.context.get("set_default_package", False)
        ):
            self._auto_create_delivery_package()
        return super().send_to_shipper()
