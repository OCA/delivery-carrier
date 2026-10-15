#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import math

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _fedex_rest_get_commodity(self):
        self.ensure_one()
        product = self.product_id
        picking = self.picking_id
        weight, _unit = picking._fedex_rest_convert_weight(
            product.weight * self.qty_done
        )
        country = product.origin_country_id or picking.company_id.country_id
        return {
            "description": product.display_name,
            "quantity": max(1, math.ceil(self.qty_done)),
            "unitPrice": self.get_unit_price_for_customs(),
            "weight": weight,
            "countryOfManufacture": country.code or "",
            "harmonizedCode": product.get_hs_code_recursively().hs_code or "",
        }
