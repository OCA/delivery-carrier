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
from pdf_utils import assemble_pdf
from openerp.osv import orm


class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def get_pdf_label(self, cr, uid, ids, context=None):
        """ Return a single pdf of labels for a stock picking

        If more than one label is found for a picking we merge one label per
        tracking in a single pdf

        :return: a list of pdf file data
        """
        res = dict.fromkeys(ids, False)
        label_obj = self.pool.get('shipping.label')
        for picking_id in ids:
            label_ids = label_obj.search(cr, uid,
                                         [('file_type', '=', 'pdf'),
                                          ('res_id', '=', picking_id)],
                                         order='create_date',
                                         context=context)
            if label_ids:
                all_picking_labels = label_obj.browse(cr, uid,
                                                      label_ids,
                                                      context=context)

                tracking_ids = [l.tracking_id for l in all_picking_labels]

                # filter for newest created label for each trackings
                label_datas = []
                tracking_ids = set(tracking_ids)
                while tracking_ids:
                    tracking_id = tracking_ids.pop()
                    for label in all_picking_labels:
                        if label.tracking_id.id == tracking_id.id:
                            label_datas.append(label.datas.decode('base64'))

                label_pdf = assemble_pdf(label_datas)
                res[picking_id] = label_pdf.encode('base64')
        return res
