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
        for picking in self.browse(cr, uid, ids, context=context):
            label_ids = label_obj.search(cr, uid,
                                         [('file_type', '=', 'pdf'),
                                          ('res_id', '=', picking.id)],
                                         order='create_date DESC',
                                         context=context)
            if label_ids:
                pack_tracking_ids = set([line.tracking_id.id
                                         for line in picking.move_lines])
                all_picking_labels = label_obj.browse(cr, uid,
                                                      label_ids,
                                                      context=context)

                tracking_ids = [l.tracking_id for l in all_picking_labels]

                # filter for newest created label for each trackings
                # and tracking existing in pack linked to a move line
                # of current picking
                label_datas = []
                tracking_register = []
                while tracking_ids:
                    tracking_id = tracking_ids.pop()
                    for label in all_picking_labels:
                        if (label.tracking_id.id == tracking_id.id
                                and (not tracking_id
                                     or tracking_id.id in pack_tracking_ids)
                                and tracking_id.id not in tracking_register):
                            label_datas.append(label.datas.decode('base64'))
                            tracking_register.append(tracking_id.id)

                label_pdf = assemble_pdf(label_datas)
                res[picking.id] = label_pdf.encode('base64')
        return res
