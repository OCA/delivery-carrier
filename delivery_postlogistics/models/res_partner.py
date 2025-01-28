# Copyright 2013 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    delivery_carrier_template_option_ids = fields.Many2many(
        "delivery.carrier.template.option",
        relation="delivery_carrier_template_options_res_partners_rel",
        column1="partner_id",
        column2="option_id",
        string="Postlogistics Options",
    )

    postlogistics_notification = fields.Selection(
        [
            ("disabled", "Disabled"),
            ("email", "Email"),
            ("sms", "Mobile SMS"),
            ("phone", "Phone Call"),
        ],
        default="disabled",
    )
