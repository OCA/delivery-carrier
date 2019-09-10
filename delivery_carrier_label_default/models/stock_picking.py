# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import base64

from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def generate_default_label(self):
        """Generate a label from a qweb report."""
        self.ensure_one()
        report = self.env.ref('delivery_carrier_label_default.default_label')
        file_, file_type = report.render(res_ids=self.ids)
        return {
            'name': '%s.%s' % (report.name, file_type),
            'file': base64.b64encode(file_),
            'file_type': file_type,
        }
