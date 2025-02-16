# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import base64

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def generate_default_label(self):
        """Generate a label from a qweb report."""
        self.ensure_one()
        report = self.env.ref(
            "delivery_carrier_label_default.action_report_default_label"
        )
        file_, file_type = report._render(report.report_name, res_ids=self.ids)
        return {
            "name": f"{report.name}.{file_type}",
            "file": base64.b64encode(file_),
            "file_type": file_type,
        }
