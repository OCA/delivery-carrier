# coding: utf-8
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    def open_tracking_url(self):
        self.ensure_one()
        if self.result_package_id and self.result_package_id.parcel_tracking:
            return self.result_package_id.open_tracking_url()
        return None
