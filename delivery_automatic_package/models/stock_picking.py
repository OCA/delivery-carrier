# Copyright 2019 Akretion <https://www.akretion.com>.
# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

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
            self._set_a_default_package()
        return super().send_to_shipper()
