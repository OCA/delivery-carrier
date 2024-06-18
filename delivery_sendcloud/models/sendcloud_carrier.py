# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import api, fields, models


class SendcloudCarrier(models.Model):
    _name = "sendcloud.carrier"
    _description = "Sendcloud Carrier"

    name = fields.Char(required=True)
    sendcloud_code = fields.Char(required=True)

    @api.model
    def _create_update_carriers(self, retrieved_carriers):
        all_carriers = self.search([])
        existing_carriers = all_carriers.mapped("sendcloud_code")
        to_add_carriers = set(retrieved_carriers) - set(existing_carriers)
        new_carrier_vals_list = []
        for new_carrier in list(to_add_carriers):
            vals = {"sendcloud_code": new_carrier, "name": new_carrier.upper()}
            new_carrier_vals_list.append(vals)
        self.create(new_carrier_vals_list)
