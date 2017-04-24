# -*- coding: utf-8 -*-
# © 2012 Guewen Baconnier (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api, fields


class DeliveryCarrierFileGenerate(models.TransientModel):

    _name = 'delivery.carrier.file.generate'

    @api.model
    def _get_picking_ids(self):
        context = self.env.context
        res = False
        if (context.get('active_model', False) == 'stock.picking' and
                context.get('active_ids', False)):
            res = context['active_ids']
        return res

    picking_ids = fields.Many2many(
        comodel_name='stock.picking',
        string='Delivery Orders',
        default=_get_picking_ids,
        required=True)
    recreate = fields.Boolean(
        string='Recreate files',
        help="If this option is used, new files will be generated "
             "for selected picking even if they already had one.\n"
             "By default, delivery orders with existing file will be "
             "skipped.")

    @api.multi
    def action_generate(self):
        """
        Call the creation of the delivery carrier files
        """
        self.ensure_one()

        self.picking_ids.generate_carrier_files(
            auto=False,
            recreate=self.recreate)

        return {'type': 'ir.actions.act_window_close'}
