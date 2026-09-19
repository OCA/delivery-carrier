# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import json

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDeliveryPackageTracking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Parcel Carrier",
                "delivery_type": "fixed",
                "product_id": cls.env["product.product"]
                .create({"name": "Shipping", "type": "service"})
                .id,
                "package_tracking_required": True,
                "tracking_url": "https://carrier.example.com/track/<shipmenttrackingnumber>",
            }
        )
        cls.products = cls.env["product.product"].create(
            [
                {"name": "Helmet", "is_storable": True},
                {"name": "Boots", "is_storable": True},
            ]
        )
        for product in cls.products:
            cls.env["stock.quant"]._update_available_quantity(
                product, cls.warehouse.lot_stock_id, 10
            )
        cls.customer = cls.env["res.partner"].create({"name": "Customer"})

    def _delivery(self, carrier=None, picking_type=None):
        picking_type = picking_type or self.warehouse.out_type_id
        source = picking_type.default_location_src_id
        destination = picking_type.default_location_dest_id
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.customer.id,
                "picking_type_id": picking_type.id,
                "location_id": source.id,
                "location_dest_id": destination.id,
                "carrier_id": (carrier or self.carrier).id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": 2,
                            "location_id": source.id,
                            "location_dest_id": destination.id,
                        }
                    )
                    for product in self.products
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.picked = True
        return picking

    def _pack_each_line(self, picking):
        packages = self.env["stock.package"]
        for line in picking.move_line_ids:
            package = self.env["stock.package"].create({})
            line.result_package_id = package
            packages |= package
        return packages

    def test_tracking_reference_comes_from_the_packages(self):
        picking = self._delivery()
        packages = self._pack_each_line(picking)
        self.assertFalse(picking.carrier_tracking_ref)
        packages[0].carrier_tracking_ref = "GUIDE-1"
        self.assertEqual(picking.carrier_tracking_ref, "GUIDE-1")
        packages[1].carrier_tracking_ref = "GUIDE-2"
        self.assertEqual(picking.carrier_tracking_ref, "GUIDE-1,GUIDE-2")

    def test_every_package_needs_a_reference_to_validate(self):
        picking = self._delivery()
        packages = self._pack_each_line(picking)
        packages[0].carrier_tracking_ref = "GUIDE-1"
        with self.assertRaises(UserError) as error:
            picking.button_validate()
        self.assertIn(packages[1].name, str(error.exception))
        packages[1].carrier_tracking_ref = "GUIDE-2"
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.carrier_tracking_ref, "GUIDE-1,GUIDE-2")

    def test_without_packages_the_reference_is_typed_by_hand(self):
        picking = self._delivery()
        picking.carrier_tracking_ref = "SINGLE-GUIDE"
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.carrier_tracking_ref, "SINGLE-GUIDE")

    def test_carrier_without_the_option_validates_as_before(self):
        self.carrier.package_tracking_required = False
        picking = self._delivery()
        self._pack_each_line(picking)
        picking.button_validate()
        self.assertEqual(picking.state, "done")

    def test_tracking_links_per_package(self):
        picking = self._delivery()
        packages = self._pack_each_line(picking)
        packages[0].carrier_tracking_ref = "GUIDE-1"
        packages[1].carrier_tracking_ref = "GUIDE-2"
        self.assertEqual(
            packages[0].carrier_tracking_url,
            "https://carrier.example.com/track/GUIDE-1",
        )
        # The delivery gets the list the native Tracking button shows.
        self.assertEqual(
            json.loads(picking.carrier_tracking_url),
            [
                ["GUIDE-1", "https://carrier.example.com/track/GUIDE-1"],
                ["GUIDE-2", "https://carrier.example.com/track/GUIDE-2"],
            ],
        )
        action = picking.open_website_url()
        self.assertEqual(action["res_model"], "stock.picking")
        self.assertIn("GUIDE-2", picking.message_ids[0].body)

    def test_single_reference_keeps_the_native_link(self):
        picking = self._delivery()
        picking.carrier_tracking_ref = "SINGLE-GUIDE"
        self.assertEqual(
            picking.carrier_tracking_url,
            "https://carrier.example.com/track/SINGLE-GUIDE",
        )

    def test_only_the_outgoing_step_checks_the_references(self):
        # Pick and pack steps are internal transfers: they validate without
        # references even when their packages have none.
        internal = self._delivery(picking_type=self.warehouse.int_type_id)
        self._pack_each_line(internal)
        internal.button_validate()
        self.assertEqual(internal.state, "done")
