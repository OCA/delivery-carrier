# Copyright 2026 arielbarreiros96 (https://github.com/arielbarreiros96)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import exceptions
from odoo.http import request, route

from odoo.addons.sale_stock.controllers.portal import SaleStockPortal


class SendcloudReturnPortal(SaleStockPortal):
    @route()
    def portal_my_picking_return_report(self, picking_id, access_token=None, **kw):
        try:
            picking_sudo = self._stock_picking_check_access(
                picking_id, access_token=access_token
            )
            url = picking_sudo._sendcloud_return_portal_url()
        except (exceptions.AccessError, exceptions.MissingError):
            url = ""
        if url:
            return request.redirect(url, local=False)
        return super().portal_my_picking_return_report(
            picking_id, access_token=access_token, **kw
        )

    def _show_report(self, model, report_type, report_ref, download=False):
        if model._name == "stock.picking" and report_ref == "stock.return_label_report":
            url = model._sendcloud_return_portal_url()
            if url:
                return request.redirect(url, local=False)
        return super()._show_report(model, report_type, report_ref, download=download)
