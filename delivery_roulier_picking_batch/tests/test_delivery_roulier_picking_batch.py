# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import TestDeliveryRoulierPickingBatchCommon


class TestDeliveryRoulierPickingBatch(TestDeliveryRoulierPickingBatchCommon):
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
        self.assertIn(f"{pkg.name}-{pkg.name}-annex_0.txt", attachments.mapped("name"))

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
        self.assertIn(f"parcel_{pkg2.name}", self.batch.carrier_tracking_ref)
        self.assertIn(f"parcel_{pkg1.name}", self.batch.carrier_tracking_ref)
        self.assertFalse(self.get_attachments(self.picking_client_1))
        self.assertFalse(self.get_attachments(self.picking_client_2))
        attachments = self.get_attachments(self.batch)
        self.assertEqual(len(attachments), 4)
        self.assertIn(f"{pkg1.name}(31.05kg)-parcel_1.zpl2", attachments.mapped("name"))
        self.assertIn(f"{pkg2.name}(43.02kg)-parcel_0.zpl2", attachments.mapped("name"))
        self.assertIn(
            f"{pkg2.name}-{pkg1.name}-annex_1.txt", attachments.mapped("name")
        )
        self.assertIn(
            f"{pkg2.name}-{pkg2.name}-annex_0.txt", attachments.mapped("name")
        )

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
        self.batch.carrier_id = self.env.ref("delivery.normal_delivery_carrier").id
        self.batch.action_done()
        pkg = self.batch.picking_ids.package_ids
        self.assertEqual(len(pkg), 0)
        self.assertFalse(self.picking_client_1.carrier_tracking_ref)
        self.assertFalse(self.picking_client_2.carrier_tracking_ref)
        self.assertFalse(self.batch.carrier_tracking_ref)
