# coding: utf-8
# © 2016 Raphael Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def _dummy_before_call(self, picking_id, request):
        request['parcel']['reference'] = (
            "%s/%s" % (
                picking_id, len(picking_id._get_packages_from_picking())
            )
        )
        return request

    def _dummy_after_call(self, picking_id, response):
        return [{
            "data": response['zpl'],
            "tracking_id": "",
            "name": picking_id.name,
        }]
