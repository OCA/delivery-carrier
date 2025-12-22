# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import base64
from unittest.mock import patch

from odoo_test_helper import FakeModelLoader

from odoo import Command, exceptions
from odoo.tools.misc import file_path

from odoo.addons.base.tests.common import BaseCommon


class TestGenerateLabels(BaseCommon, FakeModelLoader):
    """Test the wizard for delivery carrier label generation"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import DeliveryCarrierTest, PackageTypeTest

        cls.loader.update_registry(
            (
                DeliveryCarrierTest,
                PackageTypeTest,
            )
        )

        Move = cls.env["stock.move"]
        Picking = cls.env["stock.picking"]
        ShippingLabel = cls.env["shipping.label"]
        BatchPicking = cls.env["stock.picking.batch"]
        cls.DeliveryCarrierLabelGenerate = cls.env["delivery.carrier.label.generate"]
        cls.PickingBatchApplyCarrier = cls.env["picking.batch.apply.carrier"]
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        default_package_type_id = (
            cls.env["stock.package.type"].sudo().create({"name": "TEST DEFAULT"})
        )
        cls.productA = cls.env["product.product"].create(
            {"name": "Product A", "is_storable": True}
        )
        cls.productB = cls.env["product.product"].create(
            {"name": "Product B", "is_storable": True}
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.productA, cls.stock_location, 20.0
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.productB, cls.stock_location, 20.0
        )

        cls.carrier_product = cls.env["product.product"].create(
            {
                "name": "Test carrier product",
                "type": "service",
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "test",
                "test_default_package_type_id": default_package_type_id.id,
                "integration_level": "rate",  # avoid sending emails
                "product_id": cls.carrier_product.id,
            }
        )
        cls.new_carrier_product = cls.env["product.product"].create(
            {
                "name": "Test NEW carrier product",
                "type": "service",
            }
        )
        cls.new_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test NEW carrier",
                "delivery_type": "test",
                "test_default_package_type_id": default_package_type_id.id,
                "integration_level": "rate",  # avoid sending emails
                "product_id": cls.new_carrier_product.id,
            }
        )
        cls.picking_out_1 = Picking.create(
            {
                "partner_id": cls.env.ref("base.res_partner_12").id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "carrier_id": cls.carrier.id,
            }
        )

        cls.picking_out_2 = Picking.create(
            {
                "partner_id": cls.env.ref("base.res_partner_12").id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "carrier_id": cls.carrier.id,
            }
        )

        move1 = Move.create(
            {
                "name": "/",
                "picking_id": cls.picking_out_1.id,
                "product_id": cls.productA.id,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "product_uom_qty": 2,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

        move2 = Move.create(
            {
                "name": "/",
                "picking_id": cls.picking_out_2.id,
                "product_id": cls.productB.id,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "product_uom_qty": 1,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

        cls.batch = BatchPicking.create(
            {
                "name": "demo_prep001",
                "picking_ids": [
                    Command.link(cls.picking_out_1.id),
                    Command.link(cls.picking_out_2.id),
                ],
                "use_oca_batch_validation": True,
            }
        )

        cls.batch.action_confirm()
        cls.batch.action_assign()

        move1.move_line_ids[0].write({"quantity": 2, "picked": True})
        move2.move_line_ids[0].write({"quantity": 2, "picked": True})

        cls.picking_out_1._set_a_default_package()
        cls.picking_out_2._set_a_default_package()
        dummy_pdf_path = file_path("delivery_carrier_label_batch/tests/dummy.pdf")
        with open(dummy_pdf_path, "rb") as dummy_pdf:
            label = dummy_pdf.read()
            cls.shipping_label_1 = ShippingLabel.create(
                {
                    "name": "picking_out_1",
                    "res_id": cls.picking_out_1.id,
                    "package_id": move1.move_line_ids[0].result_package_id.id,
                    "res_model": "stock.picking",
                    "datas": base64.b64encode(label),
                    "file_type": "pdf",
                }
            )

            cls.shipping_label_2 = ShippingLabel.create(
                {
                    "name": "picking_out_2",
                    "res_id": cls.picking_out_2.id,
                    "package_id": move2.move_line_ids[0].result_package_id.id,
                    "res_model": "stock.picking",
                    "datas": base64.b64encode(label),
                    "file_type": "pdf",
                }
            )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        return super().tearDownClass()

    # TODO Fix this test asap
    #
    #    def test_00_action_generate_labels(self):
    #        """Check merging of pdf labels
    #
    #        Test pdf generation without multiple threading
    #
    #        """
    #        wizard = self.DeliveryCarrierLabelGenerate.with_context(
    #            active_ids=self.batch.ids, active_model="stock.picking.batch"
    #        ).create({"generate_new_labels": True})
    #
    #        wizard.action_generate_labels()
    #
    #        attachment = self.env["ir.attachment"].search(
    #            [
    #               ("res_model", "=", "stock.picking.batch"),
    #               ("res_id", "=", self.batch.id)
    #            ]
    #        )
    #
    #        self.assertEqual(len(attachment), 1)
    #        self.assertTrue(attachment.datas)
    #        self.assertTrue(attachment.name, "demo_prep001.pdf")
    #        self.assertTrue(attachment.mimetype, "application/pdf")

    def test_01_action_generate_labels_no_pack(self):
        """Check merging of pdf labels

        It shouldn't be possible to print labels when packages are missing
        """
        self.batch.picking_ids.move_line_ids.write(
            {"result_package_id": False, "package_id": False}
        )
        wizard = self.DeliveryCarrierLabelGenerate.with_context(
            active_ids=self.batch.ids, active_model="stock.picking.batch"
        ).create({})
        with self.assertRaises(exceptions.UserError):
            wizard.action_generate_labels()

    # TODO Fix this test asap
    #
    #     def test_02_action_regenerate_labels(self):
    #         """Check re-generating labels"""
    #         wizard = self.DeliveryCarrierLabelGenerate.with_context(
    #             active_ids=self.batch.ids, active_model="stock.picking.batch"
    #         ).create({"generate_new_labels": True})
    #         with patch.object(
    #             type(self.carrier), "fixed_send_shipping"
    #         ) as fixed_send_shipping:
    #             fixed_send_shipping.return_value = [
    #                 {
    #                     "exact_price": 1.0,
    #                     "tracking_number": "TEST00001",
    #                 }
    #             ]
    #             with patch.object(
    #                 type(self.batch), "purge_tracking_references"
    #             ) as purge_tracking_references:
    #                 wizard.action_generate_labels()
    #                 purge_tracking_references.assert_called()
    #
    #             attachment = self.env["ir.attachment"].search(
    #                 [
    #                     ("res_model", "=", "stock.picking.batch"),
    #                     ("res_id", "=", self.batch.id),
    #                 ]
    #             )
    #
    #             self.assertEqual(len(attachment), 1)
    #             self.assertTrue(attachment.datas)
    #             self.assertEqual(attachment.name, "demo_prep001.pdf")
    #             self.assertEqual(attachment.mimetype, "application/pdf")

    def test_03_batch_purge_tracking_reference(self):
        """Unittest: check that tracking reference purge work as expected"""
        self.batch.purge_tracking_references()
        self.assertTrue(
            all(
                [
                    not p.parcel_tracking
                    for p in self.batch.move_line_ids.result_package_id
                ]
            )
        )
        pickings = [self.picking_out_1, self.picking_out_2]
        self.assertTrue(all([not p.carrier_tracking_ref for p in pickings]))

    def test_04_action_change_carrier_purge_tracking_reference(self):
        """Functional: Check purge_tracking_reference is called as carrier is
        changed from wizard"""
        wizard = self.PickingBatchApplyCarrier.with_context(
            active_ids=self.batch.ids
        ).create({"carrier_id": self.new_carrier.id})
        with patch.object(
            type(self.batch), "purge_tracking_references"
        ) as purge_tracking_references:
            wizard.apply()
            purge_tracking_references.assert_called()
