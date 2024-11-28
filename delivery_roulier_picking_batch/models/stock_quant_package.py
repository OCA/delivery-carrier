# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    batch_id = fields.Many2one("stock.picking.batch", string="Package sent from batch")

    def _roulier_prepare_attachments(self, picking, response):
        attachments = super()._roulier_prepare_attachments(picking, response)
        if picking._is_batch_roulier():
            for attachment in attachments:
                # We need to change the attachment res_model and res_id for it
                # to be linked to the batch instead of the picking
                if attachment["res_model"] == "stock.picking":
                    attachment["res_model"] = "stock.picking.batch"
                    attachment["res_id"] = picking.batch_id.id
        return attachments
