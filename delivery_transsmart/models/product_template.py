# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class ProductTemplate(models.Model):
    """
    This model is used to hold the package types.
    https://devdocs.transsmart.com/#_packages_retrieval
    """
    _inherit = 'product.template'

    package = fields.Boolean()
    code = fields.Char()
    nr = fields.Integer('Identifier')
    description = fields.Char()
    _type = fields.Char()
    # pylint: disable=attribute-deprecated
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    is_default = fields.Boolean()

    @api.constrains('nr')
    def _constrain_nr_unique(self):
        if self.nr and self.search_count([('nr', '=', self.nr)]) > 1:
            raise ValidationError(_(
                'Package Type Identifiers must be unique.'
            ))
