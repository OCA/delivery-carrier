# Copyright 2022 FactorLibre - Jorge Martínez <jorge.martinez@factorlibre.com>
# Copyright 2022 FactorLibre - Zahra Velasco <zahra.velasco@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockPicking(models.Model):
    _inherit = "stock.picking"

    deliverea_reference = fields.Char()
    deliverea_parcel_client_code = fields.Char()

    def deliverea_get_label(self):
        self.ensure_one()
        if self.delivery_type != "deliverea":
            return
        return self.carrier_id.deliverea_get_label(self)

    def is_deliverea_pickup(self):
        self.ensure_one()
        return (
            self.carrier_id.delivery_type == "deliverea"
            and self.carrier_id.deliverea_return_label
        )

    def send_to_shipper(self):
        self.ensure_one()
        if self.is_deliverea_pickup():
            self.carrier_id.deliverea_return_shipping(self)
            self.carrier_id.deliverea_get_return_label(self)
        return super().send_to_shipper()

    @api.model
    def deliverea_update_tracking_state(self, data):
        if data.get("delivereaReference"):
            picking_id = (
                self.env["stock.picking"]
                .sudo()
                .search([("deliverea_reference", "=", data.get("delivereaReference"))])
            )
            if picking_id:
                deliverea_state = self.env["deliverea.state"].search(
                    [("code", "=", data.get("trackingCode"))]
                )
                picking_id.write(
                    {
                        "delivery_state": deliverea_state.delivery_state
                        if deliverea_state
                        else False,
                        "date_delivered": datetime.strftime(
                            datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT
                        )
                        if deliverea_state
                        and deliverea_state.delivery_state == "customer_delivered"
                        else False,
                        "carrier_tracking_url": data.get("advancedTrackingUrl"),
                        "tracking_state": "[{}] {}".format(
                            data.get("trackingCode"), data.get("trackingDetails")
                        ),
                        "tracking_state_history": (
                            picking_id.tracking_state_history or ""
                        )
                        + "- {}: [{}] {} \n".format(
                            data.get("date"),
                            data.get("trackingCode"),
                            data.get("trackingDetails"),
                        ),
                    }
                )
