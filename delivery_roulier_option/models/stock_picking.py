#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _, api, fields, models

from odoo.addons.delivery_roulier import implemented_by_carrier

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    customs_category = fields.Selection(
        selection=[
            ("gift", _("Gift")),
            ("sample", _("Samples")),
            ("commercial", _("Commercial Goods")),
            ("document", _("Documents")),
            ("other", _("Other")),
            ("return", _("Goods return")),
        ],
        default="commercial",
        help="Type of sending for the customs",
    )

    @implemented_by_carrier
    def _map_options(self):
        pass

    @implemented_by_carrier
    def _get_options(self, package):
        pass

    @api.model
    def _roulier_map_options(self):
        """Customize this mapping with your own carrier.

        Like
            return {
                'FCR': 'fcr',
                'COD': 'cod',
                'INS': 'ins',
            }
        """
        return {}

    def _roulier_get_options(self, package):
        mapping_options = self._map_options()
        options = {}
        if self.option_ids:
            for opt in self.option_ids:
                opt_key = str(opt.tmpl_option_id["code"])
                if opt_key in mapping_options:
                    options[mapping_options[opt_key]] = True
                else:
                    options[opt_key] = True
        return options
