# coding: utf-8
# Copyright 2021 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError

from .common import TestGLS, mock_gls_client


class TestGlsFlow(TestGLS):
    def test_flow(self):
        """We test the complete flow, since actions depend on each other.
           To call cancel, you need to call create before; same with the report.
        """
        # when
        self.sale_order.action_confirm()
        # then
        picking = self.sale_order.picking_ids
        self.assertEqual(picking.carrier_id, self.gls_carrier)
        self.assertEqual(picking.gls_parcel_shop, self.gls_parcel_shop)
        self.assertEqual(picking.gls_package_ref, False)

        # given
        picking.force_assign()

        # everything should be put in a package before!
        with self.assertRaises(ValidationError):
            picking.do_transfer()

        # given
        pack_operation = picking.pack_operation_ids
        pack_operation.qty_done = pack_operation.product_qty
        # when
        package_action = picking.put_in_pack()

        # then: we land on "package details" action
        package = self.env["stock.quant.package"].browse(package_action["res_id"])
        self.assertEqual(package.gls_package_ref, False)
        self.assertFalse(package.gls_picking_id)

        # given
        parcel_xmlid = "delivery_carrier_label_gls.product_packaging_gls_parcel"
        packaging_parcel = self.env.ref(parcel_xmlid)
        package.packaging_id = packaging_parcel

        # when
        with mock_gls_client():
            picking.do_transfer()

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
            self.assertTrue(package in reports.mapped("package_ids"))

            # this time it will raise since there are no new packages
            with self.assertRaises(ValidationError):
                wizard_report.get_end_of_day_report()
