# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PostlogisticsLicense(models.Model):
    _name = "postlogistics.license"
    _description = "PostLogistics Franking License"

    _order = "sequence"

    name = fields.Char(string="Description", translate=True, required=True)
    number = fields.Char(string="Number", required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    sequence = fields.Integer(
        string="Sequence",
        help="Gives the sequence on company to define priority on license "
        "when multiple licenses are available for the same group of "
        "service.",
    )
