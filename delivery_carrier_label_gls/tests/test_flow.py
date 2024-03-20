# Copyright 2021 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError, ValidationError

from .common import TestGLS, mock_gls_client


class TestGlsFlow(TestGLS):
    def test_flow(self):
        """We test the complete flow, since actions depend on each other.
        To call cancel, you need to call create before; same with the report.
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 20.0
        )
        # when
        self.order_line.product_uom_qty = 5
        self.sale_order.action_confirm()
        # then
        picking = self.sale_order.picking_ids
        self.assertEqual(picking.carrier_id, self.gls_carrier)
        self.assertEqual(picking.gls_parcel_shop, self.gls_parcel_shop)
        self.assertEqual(picking.gls_package_ref, False)

        # given
        # picking.force_assign()

        # everything should be put in a package before!
        with self.assertRaises(UserError):
            picking.button_validate()

        # given
        # pack_operation = picking.pack_operation_ids
        # pack_operation.qty_done = pack_operation.product_qty
        picking.move_ids.write({"quantity_done": 5})
        # when
        pack_action = picking.action_put_in_pack()
        pack_action_ctx = pack_action["context"]
        pack_action_model = pack_action["res_model"]

        # then: we land on "package details" action ('choose.delivery.package' wizard)
        # and we instanciate it
        self.assertEqual(pack_action["name"], "Package Details")
        self.assertEqual(pack_action_model, "choose.delivery.package")
        pack_wiz = (
            self.env["choose.delivery.package"]
            .with_context(**pack_action_ctx)
            .create({})
        )

        # given
        parcel_xmlid = "delivery_carrier_label_gls.packaging_gls_parcel"
        packaging_parcel = self.env.ref(parcel_xmlid)
        pack_wiz.delivery_package_type_id = packaging_parcel
        self.assertNotEqual(pack_wiz.shipping_weight, 0.0)
        pack_wiz.action_put_in_pack()

        # when
        with mock_gls_client():
            picking.button_validate()
        package = picking.package_ids[0]
        # then: following is true since we have only one package
        self.assertEqual(package.parcel_tracking, picking.carrier_tracking_ref)
        self.assertEqual(package.gls_package_ref, picking.gls_package_ref)

        domain = [("res_model", "=", "stock.picking"), ("res_id", "=", picking.id)]
        label = self.env["shipping.label"].search(domain)
        self.assertEqual(len(label), 1, "There should be one label for this picking.")

        # optional: we cancel and resend the package, that should cancel itself out
        with mock_gls_client():
            package.gls_cancel_shipment()
            package.gls_send_shipping_package()

        # when
        wizard_report = self.env["delivery.report.gls.wizard"].create({})
        # then
        self.assertTrue(self.gls_carrier in wizard_report.carrier_ids)

        # given
        wizard_report.carrier_ids = self.gls_carrier
        # when
        with mock_gls_client():  # two report calls within the same mock!
            reports = wizard_report._get_end_of_day_report()
            # then
            self.assertTrue(package in reports.package_ids)

            # this time it will raise since there are no new packages
            with self.assertRaises(ValidationError):
                wizard_report.get_end_of_day_report()
