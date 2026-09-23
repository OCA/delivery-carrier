#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import math

from odoo import _, models
from odoo.exceptions import UserError

from ..roulier_fedex.decoder import TRACKING_URL


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def _fedex_rest_get_parcel(self, picking):
        parcel = self._roulier_get_parcel(picking)
        if parcel["weight"] <= 0:
            raise UserError(
                _("Package %s has no weight: FedEx requires a weight.", self.name)
            )
        parcel["weight"], parcel["weightUnit"] = picking._fedex_rest_convert_weight(
            parcel["weight"]
        )
        dimensions = self._fedex_rest_get_dimensions()
        if dimensions:
            parcel["dimensions"] = dimensions
        return parcel

    def _fedex_rest_get_dimensions(self):
        self.ensure_one()
        package_type = self.package_type_id
        sizes = {
            "length": package_type.packaging_length,
            "width": package_type.width,
            "height": package_type.height,
        }
        if not all(sizes.values()):
            return {}
        length_uom = self.env[
            "product.template"
        ]._get_length_uom_id_from_ir_config_parameter()
        inch = self.env.ref("uom.product_uom_inch")
        target_uom = inch if length_uom == inch else self.env.ref("uom.product_uom_cm")
        dimensions = {
            key: math.ceil(length_uom._compute_quantity(value, target_uom))
            for key, value in sizes.items()
        }
        dimensions["unit"] = "IN" if target_uom == inch else "CM"
        return dimensions

    def _fedex_rest_before_call(self, picking, payload):
        payload = self._roulier_before_call(picking, payload)
        if picking._fedex_rest_needs_customs():
            payload["customs"] = picking._fedex_rest_get_customs(
                picking._get_account(self), self
            )
        return payload

    def _fedex_rest_get_tracking_link(self):
        return TRACKING_URL % self.parcel_tracking
