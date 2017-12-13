# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          EBII MonsieurB <monsieurb@saaslys.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import models
from odoo.addons.delivery_roulier import implemented_by_carrier

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    @implemented_by_carrier
    def _get_cash_on_delivery(self, picking):
        pass

    def _roulier_get_cash_on_delivery(self, picking):
        """ called by 'cod' option
        """
        # TODO improve to take account Sale if picking created from sale
        amount = 0
        for oper in self.get_operations():
            amount += oper.product_id.list_price * oper.product_qty
        return amount
