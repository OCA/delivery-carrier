#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          EBII MonsieurB <monsieurb@saaslys.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    @api.model
    def _get_carrier_type_selection(self):
        """Add Dpd carrier type."""
        res = super(DeliveryCarrier, self)._get_carrier_type_selection()
        res.append(
            ("dpd", "Dpd"),
        )
        return res
