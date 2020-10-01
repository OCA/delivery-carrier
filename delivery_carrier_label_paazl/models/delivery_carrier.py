# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("paazl", "Paazl")],)

    def paazl_send_shipping(self, pickings):
        return pickings._paazl_send()

    def paazl_cancel_shipment(self, pickings):
        return pickings._paazl_cancel()

    def paazl_get_tracking_link(self, picking):
        return picking._paazl_get_tracking_link()
