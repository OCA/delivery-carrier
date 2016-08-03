# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (http://www.akretion.com).
#
##############################################################################

from openerp import models, api, fields
from roulier.carriers.laposte.laposte_encoder import LAPOSTE_LABEL_FORMAT


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.model
    def _get_carrier_type_selection(self):
        """Add Dummy carrier type."""
        res = super(DeliveryCarrier, self)._get_carrier_type_selection()
        res.append(('dummy', 'DUMMY'),)
        return res

    @api.model
    def _get_label_format_selection(self):
        """Output label formats available"""
        return [(x, x) for x in LAPOSTE_LABEL_FORMAT]

    label_format = fields.Selection(
        selection='_get_label_format_selection',
        default='PDF_10x15_300dpi',
        string='Type',
        help="Label output format",)
