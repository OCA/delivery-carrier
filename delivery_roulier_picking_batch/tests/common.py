# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo_test_helper import FakeModelLoader

from odoo import fields, models
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
        "annexes": [
            {
                "name": f"{parcel['reference']}-annex_{i}",
                "type": "txt",
                "data": b"dGVzdCBhbm5leGU=",
            }
            for i, parcel in enumerate(data["parcels"])
        ],
    }


class TestDeliveryRoulierPickingBatchCommon(SavepointCase):
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
