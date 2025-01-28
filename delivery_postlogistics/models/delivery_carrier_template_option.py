# Copyright 2013 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrierTemplateOption(models.Model):
    _inherit = "delivery.carrier.template.option"

    type = fields.Selection(
        selection_add=[
            ("basic"),
            ("label_layout", "Label Layout"),
            ("output_format", "Output Format"),
            ("resolution", "Output Resolution"),
        ],
        ondelete={
            "label_layout": "set default",
            "output_format": "set default",
            "resolution": "set default",
        },
    )
