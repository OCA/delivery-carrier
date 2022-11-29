# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_carrier_account_domain(self):
        return [
            ("delivery_type", "in", self.mapped("delivery_type")),
            "|",
            ("company_id", "=", False),
            ("company_id", "in", self.mapped("company_id.id")),
            "|",
            ("carrier_ids", "=", False),
            ("carrier_ids", "in", self.mapped("carrier_id").ids),
        ]

    def _get_carrier_account(self):
        """Return a carrier suitable for the current picking"""
        domain = self._get_carrier_account_domain()
        return self.env["carrier.account"].search(
            domain,
            limit=1,
            order="company_id asc, sequence asc",
        )
