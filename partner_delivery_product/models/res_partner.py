# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_product_id = fields.Many2one(
        comodel_name='product.product',
        company_dependent=True,
        string='Delivery Product',
    )
