# -*- coding: utf-8 -*-
# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import models, api

from .postlogistics.web_service import PostlogisticsWebServiceShop


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _generate_postlogistics_label(self, webservice_class=None,
                                      tracking_ids=None):
        """ Generate post label using shop label """
        if webservice_class is None:
            webservice_class = PostlogisticsWebServiceShop
        return super(StockPicking, self)._generate_postlogistics_label(
            webservice_class=webservice_class,
            tracking_ids=tracking_ids)
