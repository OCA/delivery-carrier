# Copyright 2013-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def generate_default_label(self, package_ids=None):
        """Generate a label from a qweb report."""
        self.ensure_one()
        report = self.env.ref('delivery_carrier_label_default.default_label')
        file_, file_type = report.render(res_ids=self.ids)
        return {
            'name': '%s.%s' % (report.name, file_type),
            'file': file_,
            'file_type': file_type,
        }
