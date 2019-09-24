# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class CostCenter(models.Model):
    """
    This model is used to hold the Cost Centers, the records of this model
    are created automatically by the synchronization operation and the user
    cannot change or create anything here.
    https://devdocs.transsmart.com/#_costcenter_retrieval
    """
    _name = 'cost.center'

    name = fields.Char(related='code')
    nr = fields.Integer('Identifier')
    code = fields.Char()
    description = fields.Char()
    is_default = fields.Boolean()

    _sql_constraints = [
        ('nr_unique', 'unique(nr)', 'Identifier field should be unique.')]
