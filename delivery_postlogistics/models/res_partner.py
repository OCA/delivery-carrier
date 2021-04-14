# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    postlogistics_option_ids = fields.Many2many(
        "postlogistics.delivery.carrier.template.option",
        relation="postlogistics_options_partner_rel",
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
