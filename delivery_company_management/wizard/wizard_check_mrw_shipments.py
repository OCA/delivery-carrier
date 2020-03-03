# -*- coding: utf-8 -*-
# Copyright 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import logging
import tempfile
import base64

import xlrd
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class WizardSetChangePricesMargins(models.TransientModel):
    _name = 'delivery.check.mrw.shipments.wizard'
    _description = 'Wizard to check mrw shipments'

    file_excel = fields.Binary('Excel file from MRW')

    @api.multi
    def check_mrw_file(self):
        import wdb
        wdb.set_trace()

        mass_shippmet = self.env[self._context['active_model']].browse(self._context['active_id'])

        with tempfile.NamedTemporaryFile(suffix=".csv") as fp:
            fp.write(base64.b64decode(self.file_excel))
            with open(fp.name) as csv_file:
                reader = csv.reader(csv_file,
                                    delimiter=';',
                                    lineterminator='\n', )
                first_row = True
                try:
                    for row in reader:
                        if first_row:
                            first_row = False
                            continue
                        row[3]  # Número pedido
                        row[19]  # Remitente

                except Exception as e:
                    _logger.error("An error has been produced getting csv data")

        return {'type':'ir.actions.act_window_close'}

    def read_xls_file(self):
        fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fp.write(base64.b64decode(self.file_excel))
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
