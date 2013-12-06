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
from openerp.osv import orm


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def get_pdf_label(self, cr, uid, ids, context=None):
        res = dict.fromkeys(ids, False)
        label_obj = self.pool.get('shipping.label')
        for picking_id in ids:
            label_ids = label_obj.search(cr, uid,
                                         [('file_type', '=', 'pdf'),
                                          ('res_id', '=', picking_id)],
                                         limit=1, order='create_date',
                                         context=context)
            if label_ids:
                label = label_obj.browse(cr, uid, label_ids[0],
                                         context=context)
                res[picking_id] = label.datas
        return res
