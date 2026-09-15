# Copyright 2024 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockPutInPack(models.TransientModel):
    _inherit = "stock.put.in.pack"

    package_type_domain = fields.Binary(
        compute="_compute_package_type_domain", readonly=True
    )

    @api.depends("move_line_ids", "package_ids")
    def _compute_package_type_domain(self):
        for wizard in self:
            picking = wizard.move_line_ids.picking_id or wizard.package_ids.picking_id
            if (
                not picking
                or not picking[:1].picking_type_id.filter_package_type_on_put_in_pack
            ):
                wizard.package_type_domain = []
                continue

            carrier = picking[:1].carrier_id
            if carrier:
                package_carrier_type = carrier.delivery_type
                if package_carrier_type in ("fixed", "base_on_rule", "pricelist"):
                    package_carrier_type = "none"
            else:
                package_carrier_type = False

            wizard.package_type_domain = [
                ("package_carrier_type", "=", package_carrier_type)
            ]
