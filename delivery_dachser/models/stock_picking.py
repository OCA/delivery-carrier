# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def dachser_get_label(self):
        self.ensure_one()
        if self.delivery_type != "dachser" or not self.carrier_tracking_ref:
            return False
        return self.carrier_id.dachser_get_label(self)

    def dachser_send_to_tms(self):
        self.ensure_one()
        if self.delivery_type != "dachser":
            return False
        return self.carrier_id.dachser_send_order_to_tms(self)

    def _dachser_report_manifest_data(self):
        self.ensure_one()
        return {
            "carrier_tracking_ref": self.carrier_tracking_ref,
            "reference": (
                self.sudo().sale_id.client_order_ref or self.sudo().sale_id.name or ""
            ),
            "note": self.note[:25] + "..." if self.note else "",
            "date": self.scheduled_date.date(),
            "partner": self.partner_id.name or "",
            "zip": self.partner_id.zip or "",
            "address": (self.partner_id.street + " " + (self.partner_id.street2 or "")),
            "city": self.partner_id.city or "",
            "state": self.partner_id.state_id.name or "",
            "number_of_packages": self.number_of_packages,
            "weight": self.weight or "0",
        }
