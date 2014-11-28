# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields
from openerp.tools import file_open


class ResCompany(models.Model):
    _inherit = 'res.company'

    postlogistics_wsdl_url = fields.Char(compute='_get_wsdl_url',
                                         string='WSDL URL')
    postlogistics_username = fields.Char('Username')
    postlogistics_password = fields.Char('Password')
    postlogistics_license_ids = fields.One2many(
        comodel_name='postlogistics.license',
        inverse_name='company_id',
        string='PostLogistics Frankling License',
    )
    postlogistics_logo = fields.Binary(string='Company logo for PostLogistics')
    postlogistics_office = fields.Char(string='Post office')

    postlogistics_default_label_layout = fields.Many2one(
        comodel_name='delivery.carrier.template.option',
        string='Default label layout',
    )
    postlogistics_default_output_format = fields.Many2one(
        comodel_name='delivery.carrier.template.option',
        string='Default output format',
    )
    postlogistics_default_resolution = fields.Many2one(
        comodel_name='delivery.carrier.template.option',
        string='Default resolution',
    )

    def _get_wsdl_url(self):
        wsdl_file, wsdl_path = file_open(
            'delivery_carrier_label_postlogistics/data/barcode_v2_2_wsbc.wsdl',
            pathinfo=True)
        wsdl_url = 'file://' + wsdl_path
        for company in self:
            self.postlogistics_wsdl_url = wsdl_url
