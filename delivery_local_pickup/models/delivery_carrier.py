# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("local_pickup", "Local pickup")])
    local_address_id = fields.Many2one(
        comodel_name="res.partner", string="Local address"
    )

    def local_pickup_send_shipping(self, pickings):
        return [self.local_pickup_create_shipping(p) for p in pickings]

    def local_pickup_create_shipping(self, picking):
        return {
            "exact_price": False,
            "tracking_number": "%s (%s)" % (picking.name, picking.carrier_id.name),
        }

    def local_pickup_get_base_url(self, picking):
        """Try to get base url, similar to _replace_local_links() function in mail
        addon from mail_thread model
        """
        if "website_id" in picking.carrier_id._fields:
            return picking.carrier_id.website_id.domain
        return self.env["ir.config_parameter"].sudo().get_param("web.base.url")

    def local_pickup_get_tracking_link(self, picking):
        return "%s/local_pickup/%s" % (
            self.local_pickup_get_base_url(picking),
            picking.id,
        )

    def local_pickup_rate_shipment(self, order):
        return {
            "success": True,
            "price": 0,
            "error_message": False,
            "warning_message": False,
        }
