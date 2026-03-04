# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrierTypology(models.Model):
    _name = "delivery.carrier.typology"
    _description = "Delivery Carrier Typology"

    name = fields.Char(required=True)
    code = fields.Char()
    company_ids = fields.Many2many(
        "res.company",
        string="Companies",
        relation="delivery_carrier_typology_company_rel",
        column1="carrier_typology_id",
        column2="company_id",
    )

    carrier_id = fields.Many2one(
        "delivery.carrier",
        string="Delivery Carrier",
        required=True,
        ondelete="restrict",
    )
