# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResPartnerDeliveryInfo(models.Model):
    _name = "res.partner.delivery.info"
    _description = "Delivery Indications by Customer to Carrier"

    name = fields.Char(required=True)
    text = fields.Text(required=True)
    active = fields.Boolean(default=True)
