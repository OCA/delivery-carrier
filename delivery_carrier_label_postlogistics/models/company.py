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
        string='PostLogistics Franking License',
    )
    postlogistics_logo = fields.Binary(
        string='Company Logo on Post labels',
        help="Optional company logo to show on label.\n"
             "If using an image / logo, please note the following:\n"
             "– Image width: 47 mm\n"
             "– Image height: 25 mm\n"
             "– File size: max. 30 kb\n"
             "– File format: GIF or PNG\n"
             "– Colour table: indexed colours, max. 200 colours\n"
             "– The logo will be printed rotated counter-clockwise by 90°"
             "\n"
             "We recommend using a black and white logo for printing in "
             " the ZPL2 format.",
        )
    postlogistics_office = fields.Char(
        string='Domicile Post office',
        help="Post office which will receive the shipped goods"
    )

    postlogistics_default_label_layout = fields.Many2one(
        comodel_name='delivery.carrier.template.option',
        string='Default label layout',
        domain=[('postlogistics_type', '=', 'label_layout')],
    )
    postlogistics_default_output_format = fields.Many2one(
        comodel_name='delivery.carrier.template.option',
        string='Default output format',
        domain=[('postlogistics_type', '=', 'output_format')],
    )
    postlogistics_default_resolution = fields.Many2one(
        comodel_name='delivery.carrier.template.option',
        string='Default resolution',
        domain=[('postlogistics_type', '=', 'resolution')],
    )

    def _get_wsdl_url(self):
        wsdl_file, wsdl_path = file_open(
            'delivery_carrier_label_postlogistics/data/barcode_v2_2_wsbc.wsdl',
            pathinfo=True)
        wsdl_url = 'file://' + wsdl_path
        for company in self:
            self.postlogistics_wsdl_url = wsdl_url
