# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo_test_helper import FakeModelLoader

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase


def patched_roulier_get(carrier, method, data):
    return {
        "parcels": [
            {
                "reference": f"{parcel['reference']}({parcel['weight']}kg)-parcel_{i}",
                "tracking": {"url": "", "number": f"parcel_{parcel['reference']}_{i}"},
                "label": {
                    "name": "file",
                    "data": b"dGVzdCBsYWJlbA==",
                    "type": "zpl2",
                },
                "id": i,
            }
            for i, parcel in enumerate(data["parcels"])
        ],
        "annexes": [{"name": "Annex", "type": "txt", "data": b"dGVzdCBhbm5leGU="}],
    }


class TestDeliveryRoulierPickingBatch(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Setup Fake Roulier:
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        class FakeDeliveryCarrier(models.Model):
            _inherit = "delivery.carrier"

            delivery_type = fields.Selection(
                selection_add=[("test", "Test Carrier")],
                ondelete={"test": "set default"},
            )

        class FakeStockQuantPackage(models.Model):
            _inherit = "stock.quant.package"

            def _test_get_tracking_link(self):
                return "https://test.example.com/parcel/%s" % self.parcel_tracking

        cls.loader.update_registry((FakeDeliveryCarrier, FakeStockQuantPackage))

        cls.patch_get_carriers_action_available = patch(
            "roulier.roulier.get_carriers_action_available",
            return_value={"test": ["get_label"]},
        )
        cls.patch_get = patch("roulier.roulier.get", side_effect=patched_roulier_get)

        cls.patch_get_carriers_action_available.start()
        cls.patch_get.start()

        delivery_product = cls.env["product.product"].create(
            {"name": "test shipping product", "type": "service"}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "test",
                "product_id": delivery_product.id,
            }
        )
        cls.env["carrier.account"].create(
            {
                "name": "Test Carrier Account",
                "delivery_type": "test",
                "account": "test",
                "password": "test",
            }
        )
        cls.receiver = cls.env["res.partner"].create(
            {
                "name": "Carrier label test customer",
                "country_id": cls.env.ref("base.fr").id,
                "street": "test street",
                "street2": "test street2",
                "city": "test city",
                "phone": "0000000000",
                "email": "test@test.example.com",
                "zip": "00000",
            }
        )
        cls.other_receiver = cls.env["res.partner"].create(
            {
                "name": "Carrier label test customer 2",
                "country_id": cls.env.ref("base.fr").id,
                "street": "test street2",
                "street2": "test street2 2",
                "city": "test city2",
                "phone": "0000000002",
                "email": "test2@test.example.com",
                "zip": "00002",
            }
        )
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.picking_type_out = cls.env["ir.model.data"].xmlid_to_res_id(
            "stock.picking_type_out"
        )
        cls.productA = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "weight": 0.13,
            }
        )
        cls.productB = cls.env["product.product"].create(
            {
                "name": "Product B",
                "type": "product",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "weight": 4.25,
            }
        )

        cls.picking_client_1 = cls.env["stock.picking"].create(
            {
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "picking_type_id": cls.picking_type_out,
                "company_id": cls.env.company.id,
                "partner_id": cls.receiver.id,
            }
        )

        cls.env["stock.move"].create(
            {
                "name": cls.productA.name,
                "product_id": cls.productA.id,
                "product_uom_qty": 10,
                "product_uom": cls.productA.uom_id.id,
                "picking_id": cls.picking_client_1.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

        cls.picking_client_2 = cls.env["stock.picking"].create(
            {
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "picking_type_id": cls.picking_type_out,
                "company_id": cls.env.company.id,
                "partner_id": cls.receiver.id,
            }
        )

        cls.env["stock.move"].create(
            {
                "name": cls.productB.name,
                "product_id": cls.productB.id,
                "product_uom_qty": 10,
                "product_uom": cls.productA.uom_id.id,
                "picking_id": cls.picking_client_2.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

        cls.picking_client_3 = cls.env["stock.picking"].create(
            {
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "picking_type_id": cls.picking_type_out,
                "company_id": cls.env.company.id,
                "partner_id": cls.receiver.id,
            }
        )

        cls.env["stock.move"].create(
            {
                "name": cls.productA.name,
                "product_id": cls.productA.id,
                "product_uom_qty": 4,
                "product_uom": cls.productA.uom_id.id,
                "picking_id": cls.picking_client_3.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

        cls.env["stock.move"].create(
            {
                "name": cls.productB.name,
                "product_id": cls.productB.id,
                "product_uom_qty": 7,
                "product_uom": cls.productB.uom_id.id,
                "picking_id": cls.picking_client_3.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

        cls.batch = cls.env["stock.picking.batch"].create(
            {
                "name": "Batch 1",
                "company_id": cls.env.company.id,
                "picking_ids": [
                    (4, cls.picking_client_1.id),
                    (4, cls.picking_client_2.id),
                ],
            }
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        cls.patch_get.stop()
        cls.patch_get_carriers_action_available.stop()
        super().tearDownClass()

    def get_attachments(self, record):
        return self.env["ir.attachment"].search(
            [("res_model", "=", record._name), ("res_id", "=", record.id)]
        )

    def confirm_batch(self):
        self.env["stock.quant"]._update_available_quantity(
            self.productA, self.stock_location, 50.0
        )
        self.env["stock.quant"]._update_available_quantity(
            self.productB, self.stock_location, 50.0
        )

        self.batch.action_confirm()
        for ml in (
            self.picking_client_1.move_lines
            | self.picking_client_2.move_lines
            | self.picking_client_3.move_lines
        ):
            ml.quantity_done = ml.product_uom_qty

    def test_delivery_roulier_picking_batch_no_packages(self):
        self.confirm_batch()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.batch.carrier_id = self.carrier
        self.batch.action_done()
        # There should now be a pack
        self.assertEqual(len(self.batch.sent_package_ids), 1)
        self.assertEqual(
            self.batch.sent_package_ids, self.batch.picking_ids.package_ids
        )
        self.assertAlmostEqual(self.batch.sent_package_ids.weight, 43.8)
        self.assertAlmostEqual(self.batch.weight, 43.8)

    def test_delivery_roulier_picking_batch_no_packages_no_carrier(self):
        self.confirm_batch()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.batch.action_done()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.assertFalse(self.batch.sent_package_ids)

    def test_delivery_roulier_picking_batch_existing_packages(self):
        self.confirm_batch()
        self.picking_client_1._put_in_pack(self.picking_client_1.move_line_ids, False)
        self.picking_client_2._put_in_pack(self.picking_client_2.move_line_ids, False)
        self.assertEqual(len(self.batch.picking_ids.package_ids), 2)

        self.assertAlmostEqual(self.picking_client_1.package_ids.weight, 1.3)
        self.assertAlmostEqual(self.picking_client_2.package_ids.weight, 42.5)
        self.assertAlmostEqual(self.batch.weight, 43.8)
        packages = self.batch.picking_ids.package_ids
        self.batch.carrier_id = self.carrier
        self.batch.action_done()
        # There should now be a pack
        self.assertEqual(len(self.batch.picking_ids.package_ids), 2)
        self.assertEqual(packages, self.batch.picking_ids.package_ids)
        self.assertEqual(
            self.batch.sent_package_ids, self.batch.picking_ids.package_ids
        )

    def test_delivery_roulier_picking_batch_no_carrier(self):
        self.confirm_batch()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.assertFalse(self.get_attachments(self.batch))
        self.batch.action_done()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.assertFalse(self.picking_client_1.carrier_tracking_ref)
        self.assertFalse(self.picking_client_2.carrier_tracking_ref)
        self.assertFalse(self.batch.carrier_tracking_ref)
        self.assertFalse(self.batch.carrier_tracking_url)
        self.assertFalse(self.get_attachments(self.picking_client_1))
        self.assertFalse(self.get_attachments(self.picking_client_2))
        self.assertFalse(self.get_attachments(self.batch))

    def test_delivery_roulier_picking_batch_label(self):
        self.confirm_batch()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.assertFalse(self.get_attachments(self.batch))
        self.batch.carrier_id = self.carrier
        self.batch.action_done()
        pkg = self.batch.picking_ids.package_ids
        self.assertEqual(len(pkg), 1)
        self.assertFalse(self.picking_client_1.carrier_tracking_ref)
        self.assertFalse(self.picking_client_2.carrier_tracking_ref)
        self.assertEqual(self.batch.carrier_tracking_ref, f"parcel_{pkg.name}_0")
        self.assertEqual(
            self.batch.carrier_tracking_url,
            f"https://test.example.com/parcel/parcel_{pkg.name}_0",
        )
        self.assertFalse(self.get_attachments(self.picking_client_1))
        self.assertFalse(self.get_attachments(self.picking_client_2))
        attachments = self.get_attachments(self.batch)
        self.assertEqual(len(attachments), 2)
        self.assertIn(f"{pkg.name}(43.8kg)-parcel_0.zpl2", attachments.mapped("name"))
        self.assertIn(f"{pkg.name}-Annex.txt", attachments.mapped("name"))

    def test_delivery_roulier_picking_batch_multipackage_labels(self):
        self.batch.picking_ids |= self.picking_client_3
        self.confirm_batch()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.assertFalse(self.get_attachments(self.batch))

        self.picking_client_1._put_in_pack(
            self.picking_client_1.move_line_ids
            | self.picking_client_3.move_line_ids.filtered(
                lambda ml: ml.product_id == self.productB
            ),
            False,
        )
        self.assertEqual(len(self.batch.picking_ids.package_ids), 1)
        pkg1 = self.batch.picking_ids.package_ids
        self.picking_client_2._put_in_pack(
            self.picking_client_2.move_line_ids
            | self.picking_client_3.move_line_ids.filtered(
                lambda ml: ml.product_id == self.productA
            ),
            False,
        )
        self.assertEqual(len(self.batch.picking_ids.package_ids), 2)
        pkg2 = self.batch.picking_ids.package_ids - pkg1
        self.assertAlmostEqual(pkg1.weight, 31.05)
        self.assertAlmostEqual(pkg2.weight, 43.02)
        self.assertAlmostEqual(self.batch.weight, 74.07)

        self.batch.carrier_id = self.carrier
        self.batch.action_done()
        self.assertEqual(self.batch.picking_ids.package_ids, pkg1 | pkg2)
        self.assertFalse(self.picking_client_1.carrier_tracking_ref)
        self.assertFalse(self.picking_client_2.carrier_tracking_ref)
        self.assertIn(
            self.batch.carrier_tracking_ref,
            (
                f"parcel_{pkg1.name}_0;parcel_{pkg2.name}_0",
                f"parcel_{pkg2.name}_0;parcel_{pkg1.name}_0",
            ),
        )
        self.assertFalse(self.get_attachments(self.picking_client_1))
        self.assertFalse(self.get_attachments(self.picking_client_2))
        attachments = self.get_attachments(self.batch)
        self.assertEqual(len(attachments), 4)
        self.assertIn(f"{pkg1.name}(31.05kg)-parcel_0.zpl2", attachments.mapped("name"))
        self.assertIn(f"{pkg2.name}(43.02kg)-parcel_0.zpl2", attachments.mapped("name"))
        self.assertIn(f"{pkg1.name}-Annex.txt", attachments.mapped("name"))
        self.assertIn(f"{pkg2.name}-Annex.txt", attachments.mapped("name"))

    def test_delivery_roulier_picking_batch_multiple_receiver(self):
        self.confirm_batch()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.batch.carrier_id = self.carrier
        self.picking_client_2.partner_id = self.other_receiver
        with self.assertRaisesRegex(
            UserError, "Multiple receiver addresses found for pickings:"
        ):
            self.batch.action_done()

    def test_delivery_roulier_picking_batch_no_receiver(self):
        self.confirm_batch()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.batch.carrier_id = self.carrier
        self.picking_client_2.partner_id = False
        self.batch.action_done()
        pkg = self.batch.picking_ids.package_ids
        self.assertEqual(len(pkg), 1)
        self.assertFalse(self.picking_client_1.carrier_tracking_ref)
        self.assertFalse(self.picking_client_2.carrier_tracking_ref)
        self.assertEqual(self.batch.carrier_tracking_ref, f"parcel_{pkg.name}_0")

    def test_delivery_roulier_picking_with_same_carrier_not_confirmed(self):
        self.confirm_batch()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.picking_client_1.carrier_id = self.carrier
        self.batch.carrier_id = self.carrier
        self.batch.action_done()
        pkg = self.batch.picking_ids.package_ids
        self.assertEqual(len(pkg), 1)
        self.assertFalse(self.picking_client_1.carrier_tracking_ref)
        self.assertFalse(self.picking_client_2.carrier_tracking_ref)
        self.assertEqual(self.batch.carrier_tracking_ref, f"parcel_{pkg.name}_0")

    def test_delivery_roulier_picking_with_other_carrier_not_confirmed(self):
        self.confirm_batch()
        self.assertFalse(self.batch.picking_ids.package_ids)
        self.picking_client_1.carrier_id = self.env.ref(
            "delivery.normal_delivery_carrier"
        )
        self.batch.carrier_id = self.carrier
        with self.assertRaisesRegex(
            UserError,
            f"Pickings {self.picking_client_1.name} already have a different carrier",
        ):
            self.batch.action_done()

    def test_delivery_roulier_picking_batch_not_roulier(self):
        self.confirm_batch()
        self.assertFalse(self.batch.picking_ids.package_ids)
        with self.assertRaisesRegex(UserError, "Only Roulier carrier is supported"):
            self.batch.carrier_id = self.env.ref("delivery.normal_delivery_carrier").id
