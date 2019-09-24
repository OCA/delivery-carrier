# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields


class ServiceLevelOther(models.Model):
    """
    Used for keeping the Service Level Other records.
    https://devdocs.transsmart.com/#_service_level_other_retrieval
    """
    _name = 'service.level.other'

    name = fields.Char(related='code')
    nr = fields.Integer('Identifier')
    code = fields.Char()
    description = fields.Char()
    is_default = fields.Char()

    _sql_constraints = [
        ('nr_unique', 'unique(nr)', 'Identifier field should be unique.')]
