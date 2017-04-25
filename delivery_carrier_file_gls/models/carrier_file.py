# -*- coding: utf-8 -*-
# Copyright 2017 PESOL - Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields


class DeliveryCarrierFile(models.Model):
    _inherit = 'delivery.carrier.file'

    @api.model
    def get_type_selection(self):
        result = super(DeliveryCarrierFile, self).get_type_selection()
        gls = ('gls', 'GLS')
        if gls not in result:
            result.append(gls)
        return result

    type = fields.Selection(
        get_type_selection,
        'Type',
        required=True)
