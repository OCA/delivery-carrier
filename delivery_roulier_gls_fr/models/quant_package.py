# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


URL_TRACKING = "https://gls-group.eu/FR/fr/suivi-colis?match=%s"


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    carrier_id = fields.Many2one('delivery.carrier')

    def _gls_get_tracking_link(self):
        self.ensure_one()
        return URL_TRACKING % self.parcel_tracking

    @api.model
    def _get_sequence(self, label_name):
        sequence = self.env["ir.sequence"].next_by_code(
            "stock.picking_%s" % label_name)
        if not sequence:
            raise UserError(
                _("There is no sequence defined for the label '%s'")
                % label_name)
        return sequence

    # maybe we could implement this number stuff directly in roulier since we send
    # all packages at once.
    def _gls_fr_get_parcels(self, picking):
        res = []
        num = 0
        for pack in self:
            num += 1
            res.append(pack._gls_fr_get_parcel(picking, num))
        return res

    def _gls_fr_get_parcel(self, picking, number):
        return {
            "parcel_number_label": number,
            "parcel_number_barcode": number,
            "custom_sequence": self._get_sequence("gls"),
            "weight": "{0:05.2f}".format(self.weight)
        }
