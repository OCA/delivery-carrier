# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    delivery_state_delivered_email_validation = fields.Boolean(
        string="Email Confirmation delivered picking", default=False
    )
    delivery_state_delivered_mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template delivered picking",
        domain="[('model', '=', 'stock.picking')]",
    )
