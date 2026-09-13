# Copyright 2022 Impulso Diagonal - Javier Colmeiro
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def sending_get_label(self):
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "sending" or not tracking_ref:
            return
        label = self.carrier_id.sending_get_label(tracking_ref)
        label_name = f"sending_label_{tracking_ref}.zpl"
        self.message_post(
            body=self.env._("Sending label for %s", tracking_ref),
            attachments=[(label_name, label)],
        )
        return label
