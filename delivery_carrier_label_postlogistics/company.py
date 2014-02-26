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
from openerp.osv import orm, fields
from openerp.tools import file_open


class ResCompany(orm.Model):
    _inherit = 'res.company'

    def _get_wsdl_url(self, cr, uid, ids, field_name, arg, context=None):
        wsdl_file, wsdl_path = file_open('delivery_carrier_label_postlogistics/data/barcode_v2_2.wsdl', pathinfo=True)
        wsdl_url = 'file://' + wsdl_path
        res = dict.fromkeys(ids, wsdl_url)
        return res

    _columns = {
        'postlogistics_wsdl_url': fields.function(
            _get_wsdl_url,
            string='WSDL URL',
            type='char'),
        'postlogistics_username': fields.char('Username'),
        'postlogistics_password': fields.char('Password'),
        # XXX improve license management
        'postlogistics_license_less_1kg': fields.char('License less than 1kg'),
        'postlogistics_license_more_1kg': fields.char('License more than 1kg'),
        'postlogistics_license_vinolog': fields.char('License VinoLog'),
        'postlogistics_logo': fields.binary('Company logo for PostLogistics'),
        'postlogistics_office': fields.char('Post office'),

        'postlogistics_default_label_layout': fields.many2one(
            'delivery.carrier.template.option', 'Default label layout'),
        'postlogistics_default_output_format': fields.many2one(
            'delivery.carrier.template.option', 'Default output format'),
        'postlogistics_default_resolution': fields.many2one(
            'delivery.carrier.template.option', 'Default resolution'),
        }
