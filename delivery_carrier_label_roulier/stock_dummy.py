# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (https://www.akretion.com).
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#
##############################################################################
from openerp import models

DUMMY_CARRIER_TYPE = 'dummy'


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _dummy_is_our(self):
        return self.carrier_id.type == DUMMY_CARRIER_TYPE

    def _dummy_before_call(self, package_id, request):
        request['parcel']['reference'] = (
            "%s/%s" % (package_id, len(self._get_packages_from_picking()))
        )
        return request

    def _dummy_after_call(self, package_id, response):
        return {
            "data": response['zpl'],
            "tracking_id": "",
            "name": package_id.name,
        }
