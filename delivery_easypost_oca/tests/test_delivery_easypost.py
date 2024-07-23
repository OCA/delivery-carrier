from .common import EasypostTestBaseCase


class TestDeliveryEasypost(EasypostTestBaseCase):
    def test_easypost_oca_order_rate_shipment(self):
        self.order = self._create_sale_order(qty=5)
        res = self.carrier.easypost_oca_rate_shipment(self.order)
        self.assertTrue(res["success"])
        self.assertGreater(res["price"], 0)

    def test_easypost_oca_default_shipping(self):
        SaleOrder = self._create_sale_order(1)
        Picking = SaleOrder.picking_ids[0]
        Picking.action_assign()
        Picking.move_line_ids.write({"qty_done": 1})
        self.assertGreater(
            Picking.weight,
            0.0,
            "Picking weight should be positive.",
        )

        Picking._action_done()
        self.assertGreater(
            Picking.carrier_price,
            0.0,
            "Easypost carrying price is probably incorrect",
        )
        self.assertIsNot(
            Picking.easypost_oca_carrier_id,
            False,
            "Easypost did not return any carrier",
        )
        self.assertIsNot(
            Picking.carrier_tracking_ref,
            False,
            "Easypost did not return any tracking number",
        )
        self.assertIsNot(
            Picking.easypost_oca_tracking_url,
            False,
            "Easypost did not return any tracking url",
        )

    def test_easypost_oca_single_package_shipping(self):
        SaleOrder = self._create_sale_order(5)
        self.assertEqual(
            len(SaleOrder.picking_ids),
            1,
            "The Sales Order did not generate a picking for Easypost.",
        )
        Picking = SaleOrder.picking_ids[0]
        self.assertEqual(
            Picking.carrier_id.id,
            SaleOrder.carrier_id.id,
            "Carrier is not the same on Picking and on SO(easypost).",
        )

        Picking.action_assign()

        # First move line
        Picking.move_lines[0].write({"quantity_done": 5})
        self._put_in_pack(Picking)
        Picking.move_lines[
            0
        ].move_line_ids.result_package_id.packaging_id = self.default_packaging.id
        Picking.move_lines[0].move_line_ids.result_package_id.shipping_weight = 10.0

        self.assertGreater(
            Picking.weight,
            0.0,
            "Picking weight should be positive.(ep-fedex)",
        )
        Picking._action_done()
        self.assertGreater(
            Picking.carrier_price,
            0.0,
            "Easypost carrying price is probably incorrect(fedex)",
        )
        self.assertIsNot(
            Picking.carrier_tracking_ref,
            False,
            "Easypost did not return any tracking number (fedex)",
        )
