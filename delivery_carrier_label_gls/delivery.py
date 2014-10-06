# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#
##############################################################################

from openerp.osv import orm


class DeliveryCarrier(orm.Model):
    _inherit = 'delivery.carrier'

    def _get_carrier_type_selection(self, cr, uid, context=None):
        """ Add carrier type """
        res = super(DeliveryCarrier, self)._get_carrier_type_selection(
            cr, uid, context=context)
        res.append(('gls', 'Gls'),)
        return res
