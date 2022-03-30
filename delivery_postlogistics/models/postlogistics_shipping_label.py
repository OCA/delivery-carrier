# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PostlogisticsShippingLabel(models.Model):
    """Child class of ir attachment to identify which are labels"""

    _name = "postlogistics.shipping.label"
    _inherits = {"ir.attachment": "attachment_id"}
    _description = "Shipping Label for PostLogistics"

    file_type = fields.Char(string="File type", default="pdf")
    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Attachement",
        required=True,
        ondelete="cascade",
    )
