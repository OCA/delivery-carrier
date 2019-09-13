# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


URL_TRACKING = "https://gls-group.eu/FR/fr/suivi-colis?match=%s"


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    carrier_id = fields.Many2one('delivery.carrier')

    def _gls_get_tracking_link(self):
        self.ensure_one()
        return URL_TRACKING % self.parcel_tracking
