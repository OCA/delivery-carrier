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
import Queue
import threading
import logging

from openerp import pooler
from openerp.osv import orm, fields
from openerp.tools.translate import _

from ..pdf_utils import assemble_pdf


_logger = logging.getLogger(__name__)


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

    def _do_generate_labels(self, cr, uid, wizard, pack, picking,
                            label, context=None):
        """ Generate a label in a thread safe context

        Here we declare a specific cursor so do not launch
        too many threads
        """
        picking_out_obj = self.pool['stock.picking.out']
        # generate the label of the pack
        tracking_ids = [pack.id] if pack else None
        # create a cursor to be thread safe
        thread_cr = pooler.get_db(cr.dbname).cursor()
        try:
            picking_out_obj.generate_labels(
                thread_cr, uid, [picking.id],
                tracking_ids=tracking_ids,
                context=context)
            thread_cr.commit()
        except Exception:
            thread_cr.rollback()
            try:
                raise
            except orm.except_orm as e:
                # add information on picking and pack in the exception
                picking_name = _('Picking: %s') % picking.name
                pack_num = _('Pack: %s') % pack.name if pack else ''
                raise orm.except_orm(
                    e.name,
                    ('%s %s - %s') % (picking_name, pack_num, e.value))
        finally:
            thread_cr.close()

    def worker(self, q, q_except):
        """ A worker to generate labels

        Takes data from queue q

        And if the worker encounters errors, he will add them in
        q_except queue
        """
        while not q.empty():
            args, kwargs = q.get()
            try:
                self._do_generate_labels(*args, **kwargs)
            except Exception as e:
                q_except.put(e)
            finally:
                q.task_done()

    def _get_num_workers(self, cr, uid, context=None):
        """ Get number of worker parameter for labels generation

        Optional ir.config_parameter is `shipping_label.num_workers`
        """
        param_obj = self.pool['ir.config_parameter']
        num_workers = param_obj.get_param(cr, uid,
                                          'shipping_label.num_workers')
        if not num_workers:
            return 1
        return int(num_workers)

    def _get_all_pdf(self, cr, uid, wizard, dispatch, context=None):
        q = Queue.Queue()
        q_except = Queue.Queue()

        # create the tasks to generate labels
        for pack, moves, label in self._get_packs(cr, uid, wizard, dispatch,
                                                  context=context):
            if not label or wizard.generate_new_labels:
                picking = moves[0].picking_id
                args = (cr, uid, wizard, pack, picking, label)
                kwargs = {'context': context}
                task = (args, kwargs)
                q.put(task)

        # create few workers to parallelize label generation
        num_workers = self._get_num_workers(cr, uid, context=context)
        _logger.info('Starting %s workers to generate labels', num_workers)
        for i in range(num_workers):
            t = threading.Thread(target=self.worker, args=(q, q_except))
            t.daemon = True
            t.start()

        # wait for all tasks to be done
        q.join()

        # We will not create a partial PDF if some labels weren't
        # generated thus we raise catched exceptions by the workers
        # We will try to regroup all orm exception in one
        if not q_except.empty():

            error_count = {}
            messages = []
            while not q_except.empty():
                e = q_except.get()
                if isinstance(e, orm.except_orm):
                    if e.name not in error_count:
                        error_count[e.name] = 1
                    else:
                        error_count[e.name] += 1
                    messages.append(e.value)
                else:
                    # raise other exceptions like PoolError if
                    # too many cursor where created by workers
                    raise e
            titles = []
            for key, v in error_count.iteritems():
                titles.append('%sx %s' % (v, key))

            title = _('Errors while generating labels: ') + ' '.join(titles)
            message = _('Some labels couldn\'t be generated. Please correct '
                        'following errors and generate labels again to create '
                        'the ones which failed.\n\n'
                        ) + '\n'.join(messages)
            raise orm.except_orm(title, message)

        # create a new cursor to be up to date with what was created by workers
        join_cr = pooler.get_db(cr.dbname).cursor()
        for pack, moves, label in self._get_packs(join_cr, uid,
                                                  wizard, dispatch,
                                                  context=context):
            picking = moves[0].picking_id
            if pack:
                label = self._find_pack_label(join_cr, uid, wizard, pack,
                                              context=context)
            else:
                label = self._find_picking_label(join_cr, uid, wizard, picking,
                                                 context=context)
            if not label:
                continue  # no label could be generated
            yield label
        join_cr.close()

    def action_generate_labels(self, cr, uid, ids, context=None):
        """
        Call the creation of the delivery carrier label
        of the missing labels and get the existing ones
        Then merge all of them in a single PDF

        """
        this = self.browse(cr, uid, ids, context=context)[0]
        if not this.dispatch_ids:
            raise orm.except_orm(_('Error'), _('No picking dispatch selected'))

        attachment_obj = self.pool['ir.attachment']

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
