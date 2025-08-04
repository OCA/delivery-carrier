# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from unittest.mock import patch

from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryDropoffSite(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.delivery_product = cls.env["product.product"].create(
            {
                "name": "Delivery Product",
                "type": "service",
                "categ_id": cls.env.ref("product.product_category_all").id,
                "sale_ok": True,
                "purchase_ok": True,
                "list_price": 10.0,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "product_id": cls.delivery_product.id,
                "delivery_type": "fixed",
                "fixed_price": 10.0,
                "with_dropoff_site": True,
            }
        )
        cls.dropoff_site = cls.env["dropoff.site"].create(
            {
                "name": "Test Dropoff Site",
                "code": "TDS001",
                "carrier_id": cls.carrier.id,
                "street": "123 Test Street",
                "city": "Test City",
                "zip": "12345",
                "country_id": cls.env.ref("base.us").id,
            }
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "street": "456 Customer Street",
                "city": "Customer City",
                "zip": "67890",
                "country_id": cls.env.ref("base.us").id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )

    def test_01_create_dropoff_site(self):
        """Test creation of dropoff site"""
        self.assertTrue(self.dropoff_site.partner_id)
        self.assertEqual(self.dropoff_site.partner_id.is_dropoff_site, True)
        self.assertEqual(self.dropoff_site.partner_id.customer_rank, 0)
        self.assertEqual(self.dropoff_site.partner_id.supplier_rank, 0)

    def test_02_dropoff_site_calendar(self):
        """Test calendar functionality for dropoff site"""
        # Initially no calendar
        self.assertFalse(self.dropoff_site.calendar_id)
        # Enable calendar
        self.dropoff_site.action_enable_calendar()
        self.assertTrue(self.dropoff_site.calendar_id)
        self.assertEqual(self.dropoff_site.calendar_id.name, self.dropoff_site.name)
        # Disable calendar
        self.dropoff_site.action_disable_calendar()
        self.assertFalse(self.dropoff_site.calendar_id)

    def test_03_sale_order_dropoff(self):
        """Test sale order with dropoff site delivery"""
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "carrier_id": self.carrier.id,
                "partner_shipping_id": self.dropoff_site.partner_id.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                        }
                    )
                ],
            }
        )
        self.assertTrue(sale_order.dropoff_site_required)
        self.assertEqual(sale_order.partner_shipping_id, self.dropoff_site.partner_id)
        # Confirm order and check final shipping partner
        sale_order.action_confirm()
        picking = sale_order.picking_ids[0]
        self.assertEqual(
            picking.final_shipping_partner_id, sale_order.final_shipping_partner_id
        )

    def test_04_carrier_change(self):
        """Test changing carrier on sale order"""
        # Create new carrier without dropoff
        regular_delivery_product = self.env["product.product"].create(
            {
                "name": "Regular Delivery Product",
                "type": "service",
                "categ_id": self.env.ref("product.product_category_all").id,
                "sale_ok": True,
                "purchase_ok": True,
                "list_price": 10.0,
            }
        )
        carrier_no_dropoff = self.env["delivery.carrier"].create(
            {
                "name": "Regular Carrier",
                "product_id": regular_delivery_product.id,
                "delivery_type": "fixed",
                "fixed_price": 10.0,
                "with_dropoff_site": False,
            }
        )
        # Create sale order with dropoff
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "carrier_id": self.carrier.id,
                "partner_shipping_id": self.dropoff_site.partner_id.id,
            }
        )
        sale_order.carrier_id = carrier_no_dropoff
        sale_order.onchange_carrier_id()
        self.assertFalse(sale_order.partner_shipping_id)

    def test_05_final_shipping_partner_propagation(self):
        """Test propagation of final shipping partner through documents"""
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "carrier_id": self.carrier.id,
                "partner_shipping_id": self.dropoff_site.partner_id.id,
                "final_shipping_partner_id": self.customer.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                        }
                    )
                ],
            }
        )
        sale_order.action_confirm()
        # Check propagation to picking
        picking = sale_order.picking_ids[0]
        self.assertEqual(picking.final_shipping_partner_id, self.customer)
        # Check propagation to moves
        move = picking.move_ids[0]
        self.assertEqual(move.final_shipping_partner_id, self.customer)

    def test_06_geo_localize(self):
        """Test geo_localize function on Dropoff Site"""
        with patch.object(
            type(self.dropoff_site.partner_id), "geo_localize"
        ) as mock_geo:
            self.dropoff_site.geo_localize()
            mock_geo.assert_called_once()

    def test_07_prepare_calendar_id(self):
        """Test _prepare_calendar_id method"""
        expected_calendar_data = {"name": self.dropoff_site.name}
        self.assertEqual(
            self.dropoff_site._prepare_calendar_id(), expected_calendar_data
        )

    def test_08_partner_shipping_id_domain(self):
        """Test _compute_partner_shipping_id_domain method"""
        self.carrier.with_dropoff_site = True
        self.dropoff_site.partner_id.dropoff_site_carrier_id = self.carrier
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "carrier_id": self.carrier.id,
            }
        )
        sale_order._compute_partner_shipping_id_domain()
        self.assertEqual(
            sale_order.partner_shipping_id_domain,
            [("dropoff_site_carrier_id", "=", self.carrier.id)],
        )

    def test_09_prepare_procurement_values(self):
        """Test _prepare_procurement_values in SaleOrderLine"""
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "carrier_id": self.carrier.id,
                "final_shipping_partner_id": self.customer.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                        }
                    )
                ],
            }
        )
        sale_order.action_confirm()
        order_line = sale_order.order_line[0]
        values = order_line._prepare_procurement_values(None)
        self.assertEqual(values.get("final_shipping_partner_id"), self.customer.id)
