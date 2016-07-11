# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    external_firstname = fields.Char('Firstname')
    external_middlename = fields.Char('Middlename')
    external_lastname = fields.Char('Lastname')
