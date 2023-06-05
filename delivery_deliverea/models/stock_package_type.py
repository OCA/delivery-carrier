# Copyright 2022 FactorLibre - Jorge Martínez <jorge.martinez@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(selection_add=[("deliverea", "Deliverea")])
