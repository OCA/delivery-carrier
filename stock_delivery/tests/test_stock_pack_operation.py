# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class TestStockPackOperation(TransactionCase):

    def setUp(self):
        super(TestStockPackOperation, self).setUp()
        op_id = self.env['stock.pack.operation'].search([], limit=1)
        self.operation_id = op_id
        self.pack_id = self.env['stock.quant.package'].create({})
        self.operation_id.result_package_id = self.pack_id.id

    def test_save(self):
        """ Save should return wizard """
        res = self.operation_id.save()
        model_obj = self.env['ir.model.data']
        form_id = model_obj.xmlid_to_object(
            'stock_delivery.stock_delivery_new_view_form',
        )
        action_id = model_obj.xmlid_to_object(
            'stock_delivery.stock_delivery_new_action',
        )
        expect = {
            'name': action_id.name,
            'help': action_id.help,
            'type': action_id.type,
            'view_mode': 'form',
            'view_id': form_id.id,
            'views': [
                (form_id.id, 'form'),
            ],
            'target': 'new',
            'context': {
                'active_ids': [self.operation_id.id],
            },
            'res_model': action_id.res_model,
            'res_id': 1,
        }
        self.assertDictEqual(
            expect, res,
            'Did not get correct return view. Expect %s Got %s' % (
                expect, res,
            )
        )
