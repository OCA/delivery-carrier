# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _check_required_package_measurement(self):
        """Check the required measurement on destination pacakges."""
        packages = self.move_line_ids.mapped("result_package_id")
        packages._check_required_dimension()

    def button_validate(self):
        self._check_required_package_measurement()
        return super().button_validate()

    def _put_in_pack(self, move_line_ids, create_package_level=True):
        res = super()._put_in_pack(
            move_line_ids, create_package_level=create_package_level
        )
        package_length = self._context.get("choose_delivery_package_length", 0)
        package_width = self._context.get("choose_delivery_package_width", 0)
        package_height = self._context.get("choose_delivery_package_height", 0)
        package_weight = self._context.get("choose_delivery_package_pack_weight", 0)

        res.write(
            {
                "pack_length": package_length,
                "width": package_width,
                "height": package_height,
                "pack_weight": package_weight,
            }
        )

        return res
