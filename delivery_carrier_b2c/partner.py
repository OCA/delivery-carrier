# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Chafique DELLI <chafique.delli@akretion.com>
#    Copyright 2014 Akretion
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


class res_partner(orm.Model):
    _inherit = "res.partner"

    _columns = {
        'use_b2c_info': fields.boolean(
            'Advanced address',
            help="Display additional information for home delivery (b2c)"),
        'door_code': fields.char(
            'Door Code'),
        'door_code2': fields.char(
            'Door Code 2',),
        'intercom': fields.char(
            'Intercom',
            help="Informations for Intercom such as name "
                 "or number on the intercom"),
    }

    _defaults = {
        'use_b2c_info': False,
    }
