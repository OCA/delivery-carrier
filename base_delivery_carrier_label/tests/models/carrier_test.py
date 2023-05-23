import base64

from odoo import fields, models


class DeliveryCarrierTest(models.Model):

    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("base_delivery_carrier_label", "Base Delivery Carrier Label")],
        ondelete={"base_delivery_carrier_label": "cascade"},
    )

    def base_delivery_carrier_label_send_shipping(self, pickings):
        res = []
        for picking in pickings:
            tracking_number = "123231"
            res += [
                {
                    "tracking_number": "123231",
                    "exact_price": 0.0,
                    "labels": picking._get_base_delivery_carrier_labels(
                        tracking_base=tracking_number
                    ),
                }
            ]
        return res


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _get_base_delivery_carrier_labels(self, tracking_base):
        self.ensure_one()
        i = 1
        result = list()
        for package in self.move_line_ids.package_level_id.package_id:
            number = tracking_base + "-" + str(i)
            result.append(
                {
                    "package_id": package.id,
                    "tracking_number": number,
                    "name": number,
                    "file": base64.b64encode(b"test"),
                    "file_type": "zpl2",
                }
            )
            i += 1
        return result
