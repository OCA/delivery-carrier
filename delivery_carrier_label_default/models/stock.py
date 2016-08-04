# -*- coding: utf-8 -*-
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from openerp import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def generate_default_label(self, package_ids=None):
        """
        Generate a label from a qweb report
        """
        self.ensure_one()
        report_obj = self.env['ir.actions.report.xml']

        data = {'ids': self.id}
        report_obj = self.env['report']
        pdf_report = report_obj.get_pdf(
            self, 'delivery_carrier_label_default.report_default_label',
            data=data)

        return {'name': '%s.pdf' % "Shipping Label",  # report.report_name,
                'file': pdf_report,
                'file_type': 'pdf',
                }
