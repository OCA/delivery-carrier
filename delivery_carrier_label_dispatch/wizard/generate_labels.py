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
from operator import attrgetter
from itertools import groupby

from openerp.osv import orm, fields
from openerp.tools.translate import _

from ..pdf_utils import assemble_pdf


class DeliveryCarrierLabelGenerate(orm.TransientModel):

    _name = 'delivery.carrier.label.generate'

    def _get_dispatch_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = False
        if (context.get('active_model') == 'picking.dispatch'
                and context.get('active_ids')):
            res = context['active_ids']
        return res

    _columns = {
        'dispatch_ids': fields.many2many('picking.dispatch',
                                         string='Picking Dispatch'),
        'generate_new_labels': fields.boolean(
            'Generate new labels',
            help="If this option is used, new labels will be     "
                 "generated for the packs even if they already have one.\n"
                 "The default is to use the existing label."),
    }

    _defaults = {
        'dispatch_ids': _get_dispatch_ids,
        'generate_new_labels': False,
    }

    def _get_packs(self, cr, uid, wizard, dispatch, context=None):
        moves = sorted(dispatch.move_ids, key=attrgetter('tracking_id.name'))
        for pack, moves in groupby(moves, key=attrgetter('tracking_id')):
            pack_label = self._find_pack_label(cr, uid, wizard, pack,
                                               context=context)
            yield pack, list(moves), pack_label

    def _find_picking_label(self, cr, uid, wizard, picking, context=None):
        label_obj = self.pool['shipping.label']
        domain = [('file_type', '=', 'pdf'),
                  ('res_id', '=', picking.id),
                  ('tracking_id', '=', False),
                  ]
        label_id = label_obj.search(cr, uid, domain, order='create_date DESC',
                                    limit=1, context=context)
        if not label_id:
            return None
        return label_obj.browse(cr, uid, label_id[0], context=context)

    def _find_pack_label(self, cr, uid, wizard, pack, context=None):
        label_obj = self.pool['shipping.label']
        domain = [('file_type', '=', 'pdf'),
                  ('tracking_id', '=', pack.id),
                  ]
        label_id = label_obj.search(cr, uid, domain, order='create_date DESC',
                                    limit=1, context=context)
        if not label_id:
            return None
        return label_obj.browse(cr, uid, label_id[0], context=context)

    def _get_all_pdf(self, cr, uid, wizard, dispatch, context=None):
        for pack, moves, label in self._get_packs(cr, uid, wizard, dispatch,
                                                  context=context):
            if not label or wizard.generate_new_labels:
                picking_out_obj = self.pool['stock.picking.out']
                picking = moves[0].picking_id
                # generate the label of the pack
                if pack:
                    tracking_ids = [pack.id]
                else:
                    tracking_ids = None
                try:
                    picking_out_obj.generate_labels(
                        cr, uid, [picking.id],
                        tracking_ids=tracking_ids,
                        context=context)
                except orm.except_orm as e:
                    picking_name = _('Picking: %s') % picking.name
                    pack_num = _('Pack: %s') % pack.name if pack else ''
                    raise orm.except_orm(
                        e.name,
                        _('%s %s - %s') % (picking_name, pack_num, e.value))
                if pack:
                    label = self._find_pack_label(cr, uid, wizard, pack,
                                                  context=context)
                else:
                    label = self._find_picking_label(cr, uid, wizard, picking,
                                                     context=context)
                if not label:
                    continue  # no label could be generated
            yield label

    def action_generate_labels(self, cr, uid, ids, context=None):
        """
        Call the creation of the delivery carrier label
        of the missing labels and get the existing ones
        Then merge all of them in a single PDF

        """
        this = self.browse(cr, uid, ids, context=context)[0]
        if not this.dispatch_ids:
            raise orm.except_orm(_('Error'), _('No picking dispatch selected'))

        attachment_obj = self.pool.get('ir.attachment')

        for dispatch in this.dispatch_ids:
            labels = self._get_all_pdf(cr, uid, this, dispatch,
                                       context=context)
            labels = (label.datas for label in labels)
            labels = (label.decode('base64') for label in labels if labels)
            data = {
                'name': dispatch.name + '.pdf',
                'res_id': dispatch.id,
                'res_model': 'picking.dispatch',
                'datas': assemble_pdf(labels).encode('base64'),
            }
            attachment_obj.create(cr, uid, data, context=context)

        return {
            'type': 'ir.actions.act_window_close',
        }
