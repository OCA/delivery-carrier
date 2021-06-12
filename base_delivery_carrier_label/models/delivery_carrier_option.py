# Copyright 2012 Akretion <http://www.akretion.com>.
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DeliveryCarrierOption(models.Model):
    """Option selected for a carrier method

    Those options define the list of available pre-added and available
    to be added on delivery orders

    """

    _name = "delivery.carrier.option"
    _description = "Delivery carrier option"
    _inherits = {"delivery.carrier.template.option": "tmpl_option_id"}

    active = fields.Boolean(default=True)
    mandatory = fields.Boolean(
        help=(
            "If checked, this option is necessarily applied "
            "to the delivery order. Mandatory options show up in orange "
            "in the option widget on the picking."
        ),
    )
    by_default = fields.Boolean(
        string="Applied by Default",
        help="By check, user can choose to apply this option "
        "to each Delivery Order\n using this delivery method",
    )
    tmpl_option_id = fields.Many2one(
        comodel_name="delivery.carrier.template.option",
        string="Option",
        required=True,
        ondelete="cascade",
    )
    carrier_id = fields.Many2one(comodel_name="delivery.carrier", string="Carrier")
    readonly_flag = fields.Boolean(
        string="Readonly Flag",
        help="When True, help to prevent the user to modify some fields "
        "option (if attribute is defined in the view)",
    )
    color = fields.Integer(
        compute="_compute_color",
        help="Orange if the option is mandatory, otherwise no color",
    )

    @api.depends("mandatory")
    def _compute_color(self):
        """Show that a tag is mandatory using the color attribute"""
        for tag in self:
            tag.color = 2 if tag.mandatory else False
