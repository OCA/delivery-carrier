# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.base.tests.common import BaseCommon


class TestStockPickingCarrierFromRule(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.carrier = cls.env.ref("delivery.free_delivery_carrier")
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test Partner 001", "property_delivery_carrier_id": cls.carrier.id}
        )
        cls.product = cls.env["product.product"].create({"name": "test"})
        cls.rule = cls.env["stock.rule"].search([], limit=1)
        cls.rule.partner_address_id = cls.partner
        cls.move = cls.env["stock.move"].create(
            {
                "name": "Test Move 001",
                "product_id": cls.product.id,
                "picking_type_id": cls.picking_type_out.id,
                "product_uom_qty": 2.0,
                "product_uom": cls.product.uom_id.id,
                "location_id": cls.picking_type_out.default_location_src_id.id,
                "location_dest_id": cls.customer_location.id,
                "rule_id": cls.rule.id,
            }
        )

    def test_carrier_is_assigned_from_rule(self):
        values = self.move._get_new_picking_values()
        self.assertEqual(values["carrier_id"], self.carrier.id)
