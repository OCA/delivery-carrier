# coding: utf-8
# © 2016 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase
import base64


class TestGls(TransactionCase):
    def test_international_label(self):
        pick = self.env.ref('delivery_carrier_label_gls.stock_picking_gls1')
        pick.action_confirm()
        pick.force_assign()
        trsf_m = self.env['stock.transfer_details']
        ctx_args = {'active_ids': [pick.id], 'active_model': 'stock.picking'}
        stk_trsf = trsf_m.with_context(ctx_args).create({
            'picking_id': pick.id,
            'carrier_id': self.env.ref(
                'delivery_carrier_label_gls.delivery_carrier_gls').id,
        })
        # Package is required for GLS carrier
        package = self.env['stock.quant.package'].create({'name': 'GLS01'})
        stk_trsf.item_ids.write({'package_id': package.id})
        stk_trsf.do_detailed_transfer()
        pick.action_generate_carrier_label()
        domain = [('res_id', '=', pick.id),
                  ('file_type', '=', 'zpl2'),
                  ('res_model', '=', 'stock.picking')]
        label = self.env['shipping.label'].search(domain)
        self.assertEqual(len(label), 1,
                         "Only 1 shipping label must be in picking %s"
                         % pick.id)
        words_in_label = self._check_label(base64.decodestring(label[0].datas))
        self.assertEqual(words_in_label, 2,
                         "The attachment is not a GLS label")

    def _check_label(self, content):
        known = 0
        for string in ['Numero Colis', 'ContactId']:
            if string in content:
                known += 1
        return known
