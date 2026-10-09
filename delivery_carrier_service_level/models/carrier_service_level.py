# Copyright 2013-2020 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ServiceLevel(models.Model):
    _name = "carrier.service.level"
    _description = "Carrier service levels"
    _order = "carrier_id, code"

    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", required=True)
    code = fields.Char(string="Carrier Service Level Code")
    name = fields.Char(string="Carrier Service Level Name", required=True)
    active = fields.Boolean(default=True)
