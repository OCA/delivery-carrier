# -*- coding: utf-8 -*-
# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DeliveryCarrierFile(models.Model):
    _inherit = 'delivery.carrier.file'

    @api.model
    def get_type_selection(self):
        result = super(DeliveryCarrierFile, self).get_type_selection()
        if 'tnt_express_shipper' not in result:
            result.append(('tnt_express_shipper', 'TNT Express Shipper'))
        return result

    type = fields.Selection(get_type_selection, 'Type', required=True)
    tnt_account = fields.Char('TNT Account', size=9)
