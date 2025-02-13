# Copyright 2025 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _set_a_default_package(self):
        """Pickings using this module must have a package

        If not this method put it one silently
        """
        for picking in self:
            move_lines = picking.move_line_ids.filtered(
                lambda s: not (s.package_id or s.result_package_id)
            )
            if move_lines:
                carrier = picking.carrier_id
                fname = carrier.delivery_type + "_default_package_type_id"
                if fname not in carrier._fields:
                    default_package_type_id = self.env["stock.package.type"].browse()
                default_package_type_id = carrier[fname]
                package = self.env["stock.quant.package"].create(
                    {
                        "package_type_id": default_package_type_id
                        and default_package_type_id.id
                        or False
                    }
                )
                move_lines.write({"result_package_id": package.id})
