# coding: utf-8
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.model
    def _get_carrier_type_selection(self):
        """ Add carrier type """
        res = super(DeliveryCarrier, self)._get_carrier_type_selection()
        res.append(('gls', 'Gls'),)
        return res
