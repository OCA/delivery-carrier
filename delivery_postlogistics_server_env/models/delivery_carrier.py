# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class DeliveryCarrier(models.Model):
    _name = "delivery.carrier"
    _inherit = ["delivery.carrier", "server.env.mixin"]

    @property
    def _server_env_fields(self):
        base_fields = super()._server_env_fields
        auth_fields = {
            "postlogistics_client_id": {},
            "postlogistics_client_secret": {},
        }
        auth_fields.update(base_fields)
        return auth_fields
