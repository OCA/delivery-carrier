# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Florian da Costa <florian.dacosta@akretion.com>
#    Copyright (C) 2014-TODAY Akretion <http://www.akretion.com>.
#    Copyright 2014 Camptocamp SA
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
from openerp import models, fields, api


class CarrierAccount(models.Model):
    _name = 'carrier.account'
    _description = 'Base account datas'

    @api.model
    def _get_carrier_type(self):
        """ To inherit to add carrier type like Chronopost, Postlogistics..."""
        return []

    @api.model
    def _get_file_format(self):
        """ To inherit to add label file types"""
        return [('PDF', 'PDF'),
                ('ZPL', 'ZPL'),
                ('XML', 'XML')]

    name = fields.Char(required=True)
    account = fields.Char(string='Account Number', required=True)
    password = fields.Char(string='Account Password', required=True)
    file_format = fields.Selection(
        selection='_get_file_format',
        string='File Format',
        help="Default format of the carrier's label you want to print"
    )
    type = fields.Selection(
        selection='_get_carrier_type',
        required=True,
        help="In case of several carriers, help to know which "
             "account belong to which carrier",
    )
