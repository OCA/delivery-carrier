# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def schenker_get_label(self):
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "schenker" or not tracking_ref:
            return
        label = self.carrier_id.schenker_get_label(tracking_ref)
        label_name = "schenker_label_{}.pdf".format(tracking_ref)
        self.message_post(
            body=(_("Schenker label for %s") % tracking_ref),
            attachments=[(label_name, label)],
        )
        return label
