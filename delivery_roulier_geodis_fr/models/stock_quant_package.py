# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    geodis_cab = fields.Char(help="Barcode of the label")

    def _geodis_fr_parse_response(self, picking, response):
        res = self._roulier_parse_response(picking, response)
        i = 0
        for rec in self:
            rec.write(
                {
                    "geodis_cab": response["parcels"][i]["number"],
                    "parcel_tracking": picking.geodis_shippingid,
                }
            )
            i += 1
        # add geodis_shipping_id in res so it is written on picking.
        # it is not really a tracking number, it will actually be used to get
        # the tracking once the edi file is sent.
        # we prefer filling because the parcel tracking ref is used to display the
        # label generation button, cancel label button, etc
        res["tracking_number"] = (
            not res.get("tracking_number") and picking.geodis_shippingid or ""
        )
        return res

    def _geodis_fr_should_include_customs(self, picking):
        """Customs documents not implemented."""
        return False

    def _geodis_fr_get_tracking_link(self):
        return self.parcel_tracking_uri

    def _get_edi_pack_vals(self):
        self.ensure_one()
        return {
            "barcode": self.geodis_cab,
            "weight": self.shipping_weight or self.weight,
        }
