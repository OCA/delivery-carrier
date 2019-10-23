# Copyright 2019 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class CarrierAccount(models.Model):
    _name = "carrier.account"
    _inherit = ["carrier.account", "server.env.mixin"]

    @property
    def _server_env_fields(self):
        carrier_fields = super()._server_env_fields
        carrier_fields.update({
            "account": {},
            "password": {},
            "file_format": {},
        })
        return carrier_fields

    @api.model
    def _server_env_global_section_name(self):
        """Name of the global section in the configuration files

        Can be customized in your model
        """
        return 'carrier_account'
