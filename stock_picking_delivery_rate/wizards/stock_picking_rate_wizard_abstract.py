# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models, fields


class StockPickingRateWizardAbstract(models.TransientModel):
    """ Purchase a set of stock rates """

    _name = "stock.picking.rate.wizard.abstract"
    _description = 'Stock Picking Dispatch Rate Wizard (Abstract)'

    rate_ids = fields.Many2many(
        string='Rates',
        readonly=True,
        comodel_name='stock.picking.rate',
        default=lambda s: s._default_rate_ids(),
    )

    @api.model
    def _default_rate_ids(self):
        model = 'stock.picking.rate.purchase'
        if self.env.context.get('active_model') != model:
            return None
        return [(6, 0, self.env.context.get('active_ids'))]

    @api.multi
    def action_show_wizard(self):
        """Utility method to show the wizard."""
        self.ensure_one()
        action = self.get_formview_action()
        action.update({
            'target': 'new',
        })
        return action

    @api.multi
    def action_show_purchases(self, purchase_orders):
        """Utility method to show the purchase order action."""
        model_obj = self.env['ir.model.data']
        form_id = model_obj.xmlid_to_object(
            'purchase.purchase_order_form'
        )
        tree_id = model_obj.xmlid_to_object(
            'purchase.purchase_order_tree'
        )
        action_id = model_obj.xmlid_to_object(
            'purchase.purchase_form_action'
        )
        return {
            'name': action_id.name,
            'help': action_id.help,
            'type': action_id.type,
            'view_mode': 'tree',
            'view_id': tree_id.id,
            'views': [
                (tree_id.id, 'tree'),
                (form_id.id, 'form'),
            ],
            'target': 'current',
            'context': self.env.context,
            'res_model': action_id.res_model,
            'res_ids': purchase_orders.ids,
            'domain': [('id', 'in', purchase_orders.ids)],
        }
