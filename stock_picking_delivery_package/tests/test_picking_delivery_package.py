# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests.common import TransactionCase


class TestStockPickingDeliveryPackage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_move_obj = cls.env["stock.move"]
        cls.warehouse.delivery_steps = "pick_ship"
        cls.pick_type = cls.warehouse.pick_type_id

        cls.location_out = cls.env.ref("stock.stock_location_output")
        cls.location_customers = cls.env.ref("stock.stock_location_customers")

        cls.delivery_product = cls.env["product.product"].create(
            {
                "name": "Delivery Test",
                "type": "service",
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Delivery Test",
                "product_id": cls.delivery_product.id,
            }
        )

        cls.route = cls.env["stock.route"].search(
            [
                ("rule_ids.location_dest_id", "=", cls.location_customers.id),
                ("rule_ids.location_src_id", "=", cls.location_out.id),
            ],
            limit=1,
        )
        cls.rule_out = cls.route.rule_ids.filtered(
            lambda r: r.location_dest_id == cls.location_customers
        )

        cls.pick_type.launch_delivery_package_wizard = True
        cls.package_type = cls.env["stock.package.type"].create(
            {"name": "Package Type A"}
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Test",
                "type": "product",
                "route_ids": [Command.link(cls.route.id)],
            }
        )
        cls._create_qty()
        cls.group = cls.env["procurement.group"].create({"name": "Test"})
        cls.env["procurement.group"].run(
            [
                cls.group.Procurement(
                    cls.product,
                    2.0,
                    cls.product.uom_id,
                    cls.location_customers,
                    cls.product.name,
                    "test",
                    cls.warehouse.company_id,
                    {},
                )
            ]
        )
        cls.move_pick = cls.stock_move_obj.search(
            [
                ("product_id", "=", cls.product.id),
                ("location_dest_id", "=", cls.location_out.id),
            ]
        )
        cls.move_out = cls.stock_move_obj.search(
            [
                ("product_id", "=", cls.product.id),
                ("location_dest_id", "=", cls.location_customers.id),
            ]
        )
        cls.move_out.picking_id.carrier_id = cls.carrier

    @classmethod
    def _create_qty(cls):
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": cls.product.id,
                "inventory_quantity": 10.0,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
            }
        )._apply_inventory()

    def test_picking_delivery(self):
        result = self.move_pick.picking_id.action_put_in_pack()
        self.assertEqual(result.get("res_model"), "choose.delivery.package")
