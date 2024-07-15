# Copyright 2021 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _send_confirmation_email(self):
        for pick in self.filtered(
            lambda r: r.carrier_id.integration_level == "rate_and_ship"
            and r.picking_type_code == "incoming"
        ):
            pick.purchase_send_to_shipper()
        return super()._send_confirmation_email()

    def purchase_send_to_shipper(self):
        self.ensure_one()
        res = self.carrier_id.purchase_send_shipping(self)[0]
        if (
            self.carrier_id.free_over
            and self.purchase_id
            and self.purchase_id.amount_total >= self.carrier_id.amount
        ):
            res["exact_price"] = 0.0
        self.carrier_price = res["exact_price"] * (
            1.0 + (self.carrier_id.margin / 100.0)
        )
        if res["tracking_number"]:
            self.carrier_tracking_ref = res["tracking_number"]
        order_currency = self.purchase_id.currency_id or self.company_id.currency_id
        msg = _(
            "Shipment sent to carrier %(carrier_name)s for shipping with tracking "
            "number %(tracking_ref)s<br/>Cost: %(carrier_price)s %(currency_name)s"
        ) % (
            {
                "carrier_name": self.carrier_id.name,
                "tracking_ref": self.carrier_tracking_ref,
                "carrier_price": "%.2f" % self.carrier_price,
                "currency_name": order_currency.name,
            }
        )
        self.message_post(body=msg)
        self._add_delivery_cost_to_po()

    def _add_delivery_cost_to_po(self):
        self.ensure_one()
        if self.purchase_id and self.carrier_price:
            carrier_price = self.carrier_price
            # Re-set carrier price
            if self.carrier_id.invoice_policy == "real":
                carrier_price = self.carrier_price * (
                    1.0 + (float(self.carrier_id.margin) / 100.0)
                )
            # Create delivery line allways
            line = self.purchase_id._create_delivery_line(
                self.carrier_id, carrier_price
            )
            line.delivery_picking_orig_id = self
            self.purchase_id.write({"carrier_id": self.carrier_id})
