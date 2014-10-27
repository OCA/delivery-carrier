# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Florian da Costa <florian.dacosta@akretion.com>
#    Copyright (C) 2014-TODAY Akretion <http://www.akretion.com>.
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
from openerp.osv import orm, fields


class CarrierAccount(orm.Model):
    _name = 'carrier.account'
    _description = 'Base account datas'

    def _get_carrier_type(self, cr, uid, context=None):
        """ To inherit to add carrier type like Chronopost, Postlogistics..."""
        return []

    def __get_carrier_type(self, cr, uid, context=None):
        """ Wrapper to preserve inheritance for selection field """
        return self._get_carrier_type(cr, uid, context=context)

    def _get_file_format(self, cr, uid, context=None):
        """ To inherit to add label file types"""
        return [('PDF', 'PDF'),
                ('ZPL', 'ZPL'),
                ('XML', 'XML')]

    def __get_file_format(self, cr, uid, context=None):
        """ Wrapper to preserve inheritance for selection field """
        return self._get_file_format(cr, uid, context=context)

    _columns = {
        'name': fields.char('Name', required=True),
        'account': fields.char('Account Number', required=True),
        'password': fields.char('Account Password', required=True),
        'file_format': fields.selection(
            __get_file_format, 'File Format',
            help="Default format of the carrier's label you want to print"),
        'type': fields.selection(
            __get_carrier_type, 'Type', required=True,
            help="In case of several carriers, help to know which "
                 "account belong to which carrier"),
    }
