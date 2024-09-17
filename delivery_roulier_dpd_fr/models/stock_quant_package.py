# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def _dpd_fr_get_tracking_link(self):
        return "http://www.dpd.fr/traces_%s" % self.parcel_tracking
