# Copyright 2023 FactorLibre - Jorge Martínez <jorge.martinez@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DelivereaDistributionCenter(models.Model):
    _name = "deliverea.distribution.center"

    uuid = fields.Char()
    active = fields.Boolean()
    name = fields.Char(string="Distribution Center")
    address = fields.Char()
    city = fields.Char()
    zip = fields.Char()
    country_id = fields.Many2one("res.country", string="Country")
    observations = fields.Char()
    phone = fields.Char()
    email = fields.Char()
    latitude = fields.Char()
    longitude = fields.Char()
    billing_account = fields.Char(string="Billing Account Id")
