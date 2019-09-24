# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class ResPartner(models.Model):
    """
    Delivery Carriers will be saved here.
    https://devdocs.transsmart.com/#_carriers_retrieval
    """
    _inherit = 'res.partner'

    nr = fields.Integer('Identifier')
    code = fields.Char()
    carrier = fields.Boolean()
    package_type_id = fields.Many2one('product.template')

    _sql_constrains = [
        ('nr_unique', 'unique(nr)', 'Identifier must be unique.')]
