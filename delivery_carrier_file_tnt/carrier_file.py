# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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

from odoo import api, fields, models


class CarrierFile(models.Model):
    _inherit = 'delivery.carrier.file'

    @api.model
    def get_type_selection(self):
        result = super(CarrierFile, self
                       ).get_type_selection()
        if 'tnt_express_shipper' not in result:
            result.append(('tnt_express_shipper', 'TNT Express Shipper'))
        return result

    type = fields.Selection(get_type_selection, 'Type', required=True)
    tnt_account = fields.Char('TNT Account', size=9)

CarrierFile()
