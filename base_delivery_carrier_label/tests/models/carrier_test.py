from odoo import fields, models


# pylint: disable=consider-merging-classes-inherited
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
