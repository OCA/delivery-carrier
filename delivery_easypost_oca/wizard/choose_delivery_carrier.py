import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    easypost_oca_carrier_name = fields.Char()
    easypost_oca_shipment_id = fields.Char()
    easypost_oca_rate_id = fields.Char()

    def _get_shipment_rate(self):
        vals = self.carrier_id.rate_shipment(self.order_id)
        if vals.get("success"):
            self.write(
                {
                    "easypost_oca_carrier_name": vals.get("easypost_oca_carrier_name"),
                    "easypost_oca_shipment_id": vals.get("easypost_oca_shipment_id"),
                    "easypost_oca_rate_id": vals.get("easypost_oca_rate_id"),
                }
            )
        return super()._get_shipment_rate()

    def button_confirm(self):
        self = self.with_context(
            easypost_oca_carrier_name=self.easypost_oca_carrier_name,
            easypost_oca_shipment_id=self.easypost_oca_shipment_id,
            easypost_oca_rate_id=self.easypost_oca_rate_id,
        )
        super(ChooseDeliveryCarrier, self).button_confirm()
