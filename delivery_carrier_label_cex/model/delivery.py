# -*- coding: utf-8 -*-
from odoo import models, api, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.model
    def _get_carrier_type_selection(self):
        """ Add CEX carrier type """
        res = super(DeliveryCarrier, self)._get_carrier_type_selection()
        res.append(('cex', 'CEX'))
        return res
