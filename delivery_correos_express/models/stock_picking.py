# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def correos_express_get_label(self):
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "correos_express" or not tracking_ref:
            return
        labels = self.carrier_id.correos_express_get_label(tracking_ref)
        if not labels:
            raise UserError(_("No label was returned"))
        is_pdf = self.carrier_id.correos_express_label_type != "2"
        decoded_labels = [
            base64.b64decode(label) if is_pdf else label for label in labels
        ]
        label_format = "pdf" if is_pdf else "txt"
        self.message_post(
            body=(_("Correos Express label for %s") % tracking_ref),
            attachments=[
                (
                    f"correos_express_{tracking_ref}_{index + 1}.{label_format}",
                    label,
                )
                for index, label in enumerate(decoded_labels)
            ],
        )
        # We return label in case it wants to be used in an inheritance
        return decoded_labels
