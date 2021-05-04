# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

POSTLOGISTICS_TYPES = [
    ("label_layout", "Label Layout"),
    ("output_format", "Output Format"),
    ("resolution", "Output Resolution"),
    ("basic", "Basic Service"),
    ("additional", "Additional Service"),
    ("delivery", "Delivery Instructions"),
    ("partner_option", "Partner Option"),
]


class DeliveryCarrierTemplateOption(models.Model):
    """ Available options for a carrier (partner) """

    _name = "postlogistics.delivery.carrier.template.option"
    _description = "Delivery carrier template option"

    partner_id = fields.Many2one(comodel_name="res.partner", string="Carrier")
    name = fields.Char(translate=True)
    code = fields.Char()
    description = fields.Char(
        help="Allow to define a more complete description than in the name field.",
    )
    postlogistics_type = fields.Selection(
        selection=POSTLOGISTICS_TYPES, string="PostLogistics option type",
    )
