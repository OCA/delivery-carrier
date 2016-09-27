# -*- coding: utf-8 -*-
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from operator import attrgetter
from itertools import groupby

from openerp import _, api, exceptions, fields, models

from ..pdf_utils import assemble_pdf


class DeliveryCarrierLabelGenerate(models.TransientModel):

    _name = 'delivery.carrier.label.generate'

    @api.multi
    def _get_batch_ids(self):
        res = False
        if (self.env.context.get('active_model') == 'stock.batch.picking' and
                self.env.context.get('active_ids')):
            res = self.env.context['active_ids']
        return res

    batch_ids = fields.Many2many(
        'stock.batch.picking',
        string='Picking Batch',
        default=_get_batch_ids)
    generate_new_labels = fields.Boolean(
        'Generate new labels',
        default=False,
        help="If this option is used, new labels will be "
             "generated for the packs even if they already have one.\n"
             "The default is to use the existing label.")

    @api.model
    def _get_packs(self, batch):
        batch.mapped('pack_operation_ids.result_package_id')
        operations = sorted(batch.pack_operation_product_ids,
                            key=attrgetter('result_package_id.name'))
        for pack, grp_operations in groupby(
                operations, key=attrgetter('result_package_id')):
            pack_label = self._find_pack_label(pack)
            yield pack, list(grp_operations), pack_label

    @api.model
    def _find_picking_label(self, picking):
        label_obj = self.pool['shipping.label']
        domain = [('file_type', '=', 'pdf'),
                  ('res_id', '=', picking.id),
                  ('package_id', '=', False)]
        return label_obj.search(domain, order='create_date DESC', limit=1)

    @api.model
    def _find_pack_label(self, pack):
        label_obj = self.env['shipping.label']
        domain = [('file_type', '=', 'pdf'),
                  ('package_id', '=', pack.id)]
        return label_obj.search(domain, order='create_date DESC', limit=1)

    @api.multi
    def _get_all_pdf(self, batch):
        self.ensure_one()
        for pack, operations, label in self._get_packs(batch):
            if not label or self.generate_new_labels:
                picking = operations[0].picking_id
                # generate the label of the pack
                if pack:
                    package_ids = [pack.id]
                else:
                    package_ids = None
                try:
                    picking.generate_labels(package_ids=package_ids)
                except exceptions.UserError as e:
                    picking_name = _('Picking: %s') % picking.name
                    pack_num = _('Pack: %s') % pack.name if pack else ''
                    raise exceptions.UserError(
                        _('%s %s - %s') % (picking_name, pack_num, e.value))
                if pack:
                    label = self._find_pack_label(pack)
                else:
                    label = self._find_picking_label(picking)
                if not label:
                    continue  # no label could be generated
            yield label

    @api.multi
    def action_generate_labels(self):
        """
        Call the creation of the delivery carrier label
        of the missing labels and get the existing ones
        Then merge all of them in a single PDF

        """
        self.ensure_one()
        if not self.batch_ids:
            raise exceptions.UserError(_('No picking batch selected'))

        for batch in self.batch_ids:
            labels = self._get_all_pdf(batch)
            labels = (label.datas for label in labels)
            labels = (label.decode('base64') for label in labels if labels)
            data = {
                'name': batch.name + '.pdf',
                'res_id': batch.id,
                'res_model': 'stock.batch.picking',
                'datas': assemble_pdf(labels).encode('base64'),
            }
            self.env['ir.attachment'].create(data)

        return {
            'type': 'ir.actions.act_window_close',
        }
