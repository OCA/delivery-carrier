# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    send_delivery_confirmation = fields.Boolean(
        string="When the delivery is done send a confirmation email "
               "to the customer with the tracking number.",
    )
