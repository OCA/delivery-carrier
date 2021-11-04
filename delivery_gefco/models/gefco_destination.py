# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class GefcoDestination(models.Model):
    _name = "gefco.destination"
    _description = "Gefco destination"

    country_code = fields.Char(string="Country Code", required=True, index=True)
    zip_code = fields.Char(string="Zip Code", required=True, index=True)
    directional_code = fields.Char(string="Directional Code", required=True)
    destination_code = fields.Char(string="Destination Code")
