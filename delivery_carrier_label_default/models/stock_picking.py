# -*- coding: utf-8 -*-
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def generate_default_label(self, package_ids=None):
        """
        Generate a label from a qweb report
        """
        self.ensure_one()
        pdf_report = self.env['report'].get_pdf(
            [self.id], 'delivery_carrier_label_default.report_default_label')
        return {
            'name': 'Shipping Label %s.pdf' % self.name,
            'file': pdf_report,
            'file_type': 'pdf',
        }
