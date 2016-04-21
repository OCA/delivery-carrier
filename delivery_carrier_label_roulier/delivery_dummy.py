# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (http://www.akretion.com).
#
##############################################################################

from openerp import models, api

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.model
    def _get_carrier_type_selection(self):
        """Add Dummy carrier type."""
        res = super(DeliveryCarrier, self)._get_carrier_type_selection()
        res.append(('dummy', 'DUMMY'),)
        return res
