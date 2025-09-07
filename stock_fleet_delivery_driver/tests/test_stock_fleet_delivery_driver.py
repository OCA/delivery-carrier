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
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
            }
        )
        product_delivery = cls.env["product.product"].create(
            {
                "name": "Test Delivery Product",
                "invoice_policy": "order",
                "type": "service",
                "list_price": 10.0,
                "categ_id": cls.env.ref("delivery.product_category_deliveries").id,
            }
        )
        cls.driver_a = cls.env["res.partner"].create({"name": "Driver A"})
        cls.vehicle_a = cls.env["fleet.vehicle"].create(
            {
                "model_id": fleet_model.id,
                "license_plate": "A123",
                "driver_id": cls.driver_a.id,
            }
        )
        cls.carrier_a = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier A",
                "fixed_price": 10,
                "delivery_type": "fixed",
                "product_id": product_delivery.id,
                "vehicle_id": cls.vehicle_a.id,
            }
        )
        cls.driver_b = cls.env["res.partner"].create({"name": "Driver B"})
        cls.vehicle_b = cls.env["fleet.vehicle"].create(
            {
                "model_id": fleet_model.id,
                "license_plate": "B123",
                "driver_id": cls.driver_b.id,
            }
        )
        cls.carrier_b = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier B",
                "fixed_price": 10,
                "delivery_type": "fixed",
                "product_id": product_delivery.id,
                "vehicle_id": cls.vehicle_b.id,
            }
        )
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

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

    def test_delivery_compute_driver(self):
        """Test compute for driver in delivery method when vehicle is set"""
        self.assertRecordValues(
            (self.carrier_a + self.carrier_b),
            [{"driver_id": self.driver_a.id}, {"driver_id": self.driver_b.id}],
        )
        self.carrier_a.vehicle_id = self.vehicle_b
        self.assertEqual(self.carrier_a.driver_id, self.driver_b)
        # Check driver isn't modified when vehicle is empty
        self.carrier_a.vehicle_id = False
        self.assertEqual(self.carrier_a.driver_id, self.driver_b)

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
        self.assertRecordValues(
            all_pickings,
            [
                {"vehicle_id": self.carrier_a.vehicle_id.id},
                {"vehicle_id": self.carrier_a.vehicle_id.id},
                {"vehicle_id": self.carrier_b.vehicle_id.id},
                {"vehicle_id": self.carrier_b.vehicle_id.id},
                {"vehicle_id": self.carrier_b.vehicle_id.id},
            ],
        )
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
        self.assertEqual(
            batch.driver_id,
            self.carrier_b.driver_id,
            "Batch should have the driver of the most used carrier",
        )
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
        self.assertEqual(
            len(
                out_pickings.filtered_domain(
                    [("driver_id", "=", self.carrier_b.driver_id.id)]
                )
            ),
            3,
            "First propagation should not change original Drivers in pickings",
        )
        # Check Vehicle and Driver are propagated when Batch is done
        batch.with_context(skip_sanity_check=True).action_done()
        self.assertEqual(
            out_pickings.vehicle_id,
            self.carrier_b.vehicle_id,
            "Vehicle should be propagated to original pickings when batch is done",
        )
        self.assertEqual(
            out_pickings.driver_id,
            self.carrier_b.driver_id,
            "Driver should be propagated to original pickings when batch is done",
        )
        # Check Vehicle is propagated when changed in the batch
        batch.vehicle_id = self.carrier_a.vehicle_id
        batch.driver_id = self.carrier_a.driver_id
        self.assertEqual(
            out_pickings.vehicle_id,
            self.carrier_a.vehicle_id,
            "Vehicle should be propagated to pickings when changed in the batch",
        )
        self.assertEqual(
            out_pickings.driver_id,
            self.carrier_a.driver_id,
            "Driver should be propagated to pickings when changed in the batch",
        )

    def test_auto_batch_by_vehicle(self):
        """Test an auto-batch scenario with new picking type to avoid conflicts with
        existing picking types
        The pickings look like this:
        Picking_out_1           Picking_out_2           Picking_out_3
            Vehicle_a                Vehicle_b                Vehicle_a
        So as the picking type is defined to batch automatically by vehicle,
        Picking 1&3 should be batched at their confirmation, while Picking2 isn't.
        """
        # Create picking type to avoid conflicts with existing pickings with auto-batch
        # enabled grouping by partner.
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        type_special_out = self.env["stock.picking.type"].create(
            {
                "name": "Special Delivery",
                "sequence_code": "SPECOUT",
                "code": "outgoing",
                "company_id": self.env.company.id,
                "warehouse_id": warehouse.id,
                "auto_batch": True,
                "batch_group_by_vehicle": True,
            }
        )

        # Pickings need to be in 'ready' state to be auto-batchable
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 10
        )

        # Create the pickings that will be confirmed and batched afterwards
        picking_out_1 = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": type_special_out.id,
                "company_id": self.env.company.id,
                "partner_id": self.partner.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
                "carrier_id": self.carrier_a.id,
            }
        )
        picking_out_2 = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": type_special_out.id,
                "company_id": self.env.company.id,
                "partner_id": self.partner.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 3,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
                "carrier_id": self.carrier_b.id,
            }
        )
        picking_out_3 = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": type_special_out.id,
                "company_id": self.env.company.id,
                "partner_id": self.partner.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 4,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
                "carrier_id": self.carrier_a.id,
            }
        )

        all_pickings = picking_out_1 | picking_out_2 | picking_out_3
        # No pickings should have any batch before confirmation
        self.assertFalse(all_pickings.batch_id)

        all_pickings.action_confirm()
        # Now Picking 1 and 3 should be batched together, while Picking 2 is added to
        # its own batch.
        self.assertTrue(picking_out_1.batch_id)
        self.assertTrue(picking_out_3.batch_id)
        self.assertEqual(picking_out_1.batch_id.id, picking_out_3.batch_id.id)
        self.assertTrue(picking_out_2.batch_id)
        self.assertNotEqual(picking_out_2.batch_id.id, picking_out_1.batch_id.id)

    def test_auto_batch_by_driver(self):
        """Test an auto-batch scenario with new picking type to avoid conflicts with
        existing picking types
        The pickings look like this:
        Picking_out_1           Picking_out_2           Picking_out_3
            driver_a                driver_b                driver_a

        So as the picking type is defined to batch automatically by vehicle,
        Picking 1&3 should be batched at their confirmation, while Picking2 isn't.
        """
        # Create picking type to avoid conflicts with existing pickings with auto-batch
        # enabled grouping by partner.
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        type_special_out = self.env["stock.picking.type"].create(
            {
                "name": "Special Delivery",
                "sequence_code": "SPECOUT",
                "code": "outgoing",
                "company_id": self.env.company.id,
                "warehouse_id": warehouse.id,
                "auto_batch": True,
                "batch_group_by_driver": True,
            }
        )

        # Pickings need to be in 'ready' state to be auto-batchable
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 10
        )

        # Create the pickings that will be confirmed and batched afterwards
        picking_out_1 = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": type_special_out.id,
                "company_id": self.env.company.id,
                "partner_id": self.partner.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
                "carrier_id": self.carrier_a.id,
            }
        )
        picking_out_2 = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": type_special_out.id,
                "company_id": self.env.company.id,
                "partner_id": self.partner.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 3,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
                "carrier_id": self.carrier_b.id,
            }
        )
        picking_out_3 = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": type_special_out.id,
                "company_id": self.env.company.id,
                "partner_id": self.partner.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 4,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
                "carrier_id": self.carrier_a.id,
            }
        )

        all_pickings = picking_out_1 | picking_out_2 | picking_out_3
        # No pickings should have any batch before confirmation
        self.assertFalse(all_pickings.batch_id)

        all_pickings.action_confirm()
        # Now Picking 1 and 3 should be batched together, while Picking 2 is added to
        # its own batch.
        self.assertTrue(picking_out_1.batch_id)
        self.assertTrue(picking_out_3.batch_id)
        self.assertEqual(picking_out_1.batch_id.id, picking_out_3.batch_id.id)
        self.assertTrue(picking_out_2.batch_id)
        self.assertNotEqual(picking_out_2.batch_id.id, picking_out_1.batch_id.id)
