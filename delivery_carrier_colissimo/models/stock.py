# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def get_extracted_fields(self):
        res = super(StockPicking, self).get_extracted_fields()
        to_add = ['external_firstname',
                  'external_middlename',
                  'external_lastname'
                  ]
        res.extend(to_add)
        return list(set(res))

    def get_mapping_dict(self, extract_fields):
        base_dict = super(StockPicking, self).get_mapping_dict(extract_fields)
        base_dict.update({k: k.replace('external_', '') for k in
                         ['external_firstname',
                          'external_middlename',
                          'external_lastname'
                          ]})
        return base_dict
