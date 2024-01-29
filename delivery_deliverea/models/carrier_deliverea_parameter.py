# Copyright 2022 FactorLibre - Jorge Martínez <jorge.martinez@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CarrierDeliveaParameter(models.Model):
    _name = "carrier.deliverea.parameter"

    name = fields.Char(string="Parameter Name")
    type = fields.Selection(
        selection=[
            ("conditional", "Conditional"),
            ("ignored", "Ignored"),
            ("optional", "Optional"),
            ("required", "Required"),
            ("unsupported", "Unsupported"),
        ],
    )
