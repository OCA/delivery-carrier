# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import Command
from odoo.tests.common import TransactionCase


class TestDeliverFleet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        fleet_brand = cls.env["fleet.vehicle.model.brand"].create(
            {"name": "Test Fleet Brand"}
        )
        fleet_model = cls.env["fleet.vehicle.model"].create(
            {
                "name": "Test Fleet Model",
                "brand_id": fleet_brand.id,
                "vehicle_type": "car",
                "power_unit": "horsepower",
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Test Product"})
        product_delivery = cls.env["product.product"].create(
            {
                "name": "Test Delivery Product",
                "invoice_policy": "order",
                "type": "service",
                "list_price": 10.0,
                "categ_id": cls.env.ref("delivery.product_category_deliveries").id,
            }
        )
        driver_a = cls.env["res.partner"].create({"name": "Driver A"})
        vehicle_a = cls.env["fleet.vehicle"].create(
            {
                "model_id": fleet_model.id,
                "license_plate": "A123",
                "driver_id": driver_a.id,
            }
        )
        cls.carrier_a = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier A",
                "fixed_price": 10,
                "delivery_type": "fixed",
                "product_id": product_delivery.id,
                "vehicle_id": vehicle_a.id,
            }
        )
        driver_b = cls.env["res.partner"].create({"name": "Driver B"})
        vehicle_b = cls.env["fleet.vehicle"].create(
            {
                "model_id": fleet_model.id,
                "license_plate": "B123",
                "driver_id": driver_b.id,
            }
        )
        cls.carrier_b = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier B",
                "fixed_price": 10,
                "delivery_type": "fixed",
                "product_id": product_delivery.id,
                "vehicle_id": vehicle_b.id,
            }
        )

    def _create_sale(self, carrier):
        """Helper method to create a sale order with the given carrier."""
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
                "carrier_id": carrier.id,
            }
        )

    def test_sale_stock_flow(self):
        """Test the sale flow with delivery carriers and drivers."""
        sale = self._create_sale(self.carrier_a)
        sale.action_confirm()
        self.assertEqual(sale.picking_ids.vehicle_id, self.carrier_a.vehicle_id)
        sale.picking_ids.carrier_id = self.carrier_b.id
        self.assertEqual(sale.picking_ids.vehicle_id, self.carrier_b.vehicle_id)

    def test_sale_stock_batch_flow(self):
        """Test the sale flow with delivery carriers and vehicles."""
        # Create multiple sales and pickings with different carriers
        sale_1 = self._create_sale(self.carrier_a)
        sale_1.action_confirm()
        sale_2 = self._create_sale(self.carrier_a)
        sale_2.action_confirm()
        sale_3 = self._create_sale(self.carrier_b)
        sale_3.action_confirm()
        sale_4 = self._create_sale(self.carrier_b)
        sale_4.action_confirm()
        sale_5 = self._create_sale(self.carrier_b)
        sale_5.action_confirm()
        all_pickings = (sale_1 | sale_2 | sale_3 | sale_4 | sale_5).picking_ids
        all_pickings.action_confirm()
        out_pickings = all_pickings.filtered_domain(
            [("picking_type_id", "=", self.env.ref("stock.picking_type_out").id)]
        )
        self.assertEqual(len(out_pickings), 5)
        # Check propagation of the correct Vehicle to the batch
        batch_action = (
            self.env["stock.picking.to.batch"]
            .create(
                {
                    "mode": "new",
                    "is_create_draft": False,
                    "description": "Test Batch",
                }
            )
            .with_context(active_ids=out_pickings.ids)
            .attach_pickings()
        )
        batch = self.env["stock.picking.batch"].browse(batch_action["res_id"])
        self.assertEqual(len(batch.picking_ids), 5)
        self.assertEqual(
            batch.vehicle_id,
            self.carrier_b.vehicle_id,
            "Batch should have the vehicle of the most used carrier",
        )
        self.assertEqual(batch.driver_id, self.carrier_b.vehicle_id.driver_id)
        # Check Vehicle has not been modified in original pickings on first propagation
        self.assertEqual(
            len(
                out_pickings.filtered_domain(
                    [("vehicle_id", "=", self.carrier_b.vehicle_id.id)]
                )
            ),
            3,
            "First propagation should not change original Vehicles in pickings",
        )
        # Check Vehicle is propagated when Batch is done
        batch.with_context(skip_sanity_check=True).action_done()
        self.assertEqual(
            out_pickings.vehicle_id,
            self.carrier_b.vehicle_id,
            "Vehicle should be propagated to original pickings when batch is done",
        )
        # Check Vehicle is propagated when changed in the batch
        batch.vehicle_id = self.carrier_a.vehicle_id
        self.assertEqual(
            out_pickings.vehicle_id,
            self.carrier_a.vehicle_id,
            "Vehicle should be propagated to pickings when changed in the batch",
        )
