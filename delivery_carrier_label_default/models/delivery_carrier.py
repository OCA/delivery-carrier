# Copyright 2013-2019 Camptocamp SA
# Copyright 2021 Sunflower IT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import base64

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def send_shipping(self, pickings):
        # call parent chain.
        result = super().send_shipping(pickings)
        # check if parent result has label defined, if not, add default label
        # Avoid more than one default attachment to be added. (No dups)
        if "labels" not in result[0]:
            attachment = self.env["ir.attachment"].search(
                [("name", "=ilike", ("%" + pickings[0].name + "%"))]
            )
            if not attachment:
                pdf_report = self.env.ref(
                    "delivery_carrier_label_default.action_default_label"
                )._render_qweb_pdf([pickings[0].id])
                if pdf_report:
                    result[0]["labels"] = [
                        {
                            "name": "Shipping Label %s.pdf" % pickings[0].name,
                            "file": base64.b64encode(pdf_report[0]),
                            "file_type": "pdf",
                        }
                    ]
        if result is None:
            result = self.alternative_send_shipping(pickings)
        for result_dict, picking in zip(result, pickings):
            for label in result_dict.get("labels", []):
                picking.attach_shipping_label(label)
        return result
