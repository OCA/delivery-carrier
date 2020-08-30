# Copyright 2020 Akretion (https://www.akretion.com).
# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    code = fields.Char(
        help="Delivery Method Code (according to carrier)",
    )
    description = fields.Text()
