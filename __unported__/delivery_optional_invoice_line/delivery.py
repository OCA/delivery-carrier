# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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


class delivery_carrier(orm.Model):
    _inherit = 'delivery.carrier'

    _columns = {
        'do_not_create_invoice_line': fields.boolean(
            'Do not create line on invoice'),
    }


class stock_picking(orm.Model):
    _inherit = "stock.picking"

    def _prepare_shipping_invoice_line(
        self, cr, uid, picking, invoice, context=None
    ):
        res = super(stock_picking, self)._prepare_shipping_invoice_line(
            cr, uid, picking, invoice, context=context)
        if (
            picking.carrier_id
            and picking.carrier_id.do_not_create_invoice_line
        ):
            res = None
        return res
