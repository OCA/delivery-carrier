# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models, fields, _
from openerp.exceptions import ValidationError


import logging
_logger = logging.getLogger(__name__)


class StockDeliveryNew(models.TransientModel):
    """ Create a new stock delivery """
    _name = "stock.delivery.new"
    _description = 'Stock Delivery New'

    picking_ids = fields.Many2many(
        string='Picking',
        comodel_name='stock.picking',
        compute='_compute_picking_ids',
    )
    pack_operation_ids = fields.Many2many(
        string='Pack Operations',
        comodel_name='stock.pack.operation',
        readonly=True,
        default=lambda s: s._default_pack_operation_ids(),
    )
    quant_pack_id = fields.Many2one(
        string='Quant Pack',
        comodel_name='stock.quant.package',
        required=True,
    )
    delivery_pack_id = fields.Many2one(
        string='Delivery Pack',
        comodel_name='stock.delivery.pack',
    )

    @api.multi
    def _compute_picking_ids(self):
        for rec_id in self:
            rec_id.picking_ids = [(6, 0, [
                op.picking_id.id for op in rec_id.pack_operation_ids
            ])]

    @api.model
    def _default_pack_operation_ids(self):
        return [(6, 0, self.env.context.get('active_ids'))]

    @api.multi
    def action_create_delivery(self):
        """ Create a new delivery """
        self.ensure_one()
        if not self.delivery_pack_id:
            raise ValidationError(_(
                'Must assign or create a delivery pack in order to continue.',
            ))
        # @TODO: Support for multiple pickings, likely w/ constraints
        loc_id_int = self.picking_ids[0].location_id.id
        # @TODO: Better way to identify warehouse, this is sloppy as dung
        warehouse_id = self.env['stock.warehouse'].search([  # '|',
            ('lot_stock_id', 'parent_of', loc_id_int),
        ],
            limit=1,
        )
        return self.env['stock.delivery.group'].create({
            'picking_id': self.picking_ids[0].id,
            'pack_id': self.delivery_pack_id.id,
            'warehouse_id': warehouse_id.id,
            'ship_partner_id': self.picking_ids[0].partner_id.id,
        })

    @api.multi
    def action_show_wizard(self):
        """ Utility method to show the wizard
        Returns:
            Wizard action for completion of delivery packing
        """
        self.ensure_one()
        model_obj = self.env['ir.model.data']
        form_id = model_obj.xmlid_to_object(
            'stock_delivery.stock_delivery_new_view_form',
        )
        action_id = model_obj.xmlid_to_object(
            'stock_delivery.stock_delivery_new_action',
        )
        return {
            'name': action_id.name,
            'help': action_id.help,
            'type': action_id.type,
            'view_mode': 'form',
            'view_id': form_id.id,
            'views': [
                (form_id.id, 'form'),
            ],
            'target': 'new',
            'context': self.env.context,
            'res_model': action_id.res_model,
            'res_id': self.id,
        }
