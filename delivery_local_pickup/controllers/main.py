# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class DeliveryLocalPickupController(http.Controller):
    @http.route(
        ["/local_pickup/<int:picking_id>"], type="http", auth="public", website=True
    )
    def public_local_pickup_detail(
        self, picking_id, access_token=None, report_type=None, download=False, **kw
    ):
        try:
            picking_sudo = request.env["stock.picking"].sudo().browse(picking_id)
        except (AccessError, MissingError):
            return request.redirect("/")
        if picking_sudo.carrier_id.delivery_type != "local_pickup":
            return request.redirect("/")
        values = {"picking": picking_sudo}
        return request.render("delivery_local_pickup.website_local_address", values)
