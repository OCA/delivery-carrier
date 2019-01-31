# -*- coding: utf-8 -*-
# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models, fields


class SaleShop(models.Model):
    _inherit = 'sale.shop'
    
    postlogistics_logo = fields.Binary('Shop logo for PostLogistics')
