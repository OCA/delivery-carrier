# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _pre_put_in_pack_hook(self, move_line_ids):
        """
        If the feature is enabled on picking type level, launch the
        Choose Delivery Package wizard. As the default behaviour in delivery module
        is to rely on carrier_id value (that we don't have in other operations than OUT).
        """
        if self.ship_carrier_id and self.picking_type_id.launch_delivery_package_wizard:
            result = self._set_delivery_package_type()
            context = result.get("context", {})
            if context.get("current_package_carrier_type") != "none":
                context.update(
                    {
                        "current_package_carrier_type": self.ship_carrier_id.delivery_type,
                    }
                )
            result["context"] = context
            return result
        return super()._pre_put_in_pack_hook(move_line_ids)
