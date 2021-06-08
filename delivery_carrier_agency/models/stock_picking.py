# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_domain_agency(self):
        self.ensure_one()
        wh = self.location_id.get_warehouse()
        return [
            ("delivery_type", "=", self.carrier_id.delivery_type),
            "|",
            ("warehouse_ids", "=", False),
            ("warehouse_ids", "in", wh.ids),
            "|",
            ("carrier_ids", "in", [self.carrier_id.id]),
            ("carrier_ids", "=", False),
        ]

    def _get_carrier_agency(self):
        self.ensure_one()
        domain = self._get_domain_agency()
        return self.env["delivery.carrier.agency"].search(domain, limit=1)
