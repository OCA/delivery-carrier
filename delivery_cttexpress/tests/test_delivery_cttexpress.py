# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2022 Tecnativa - David Vidal
from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestDeliveryCTTExpress(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env["product.product"].create(
            {
                "type": "service",
                "name": "Test Shipping costs",
                "list_price": 10.
            }
        )
        cls.carrier_cttexpress = cls.env["delivery.carrier"].create(
            {
                "name": "CTT Express",
                "delivery_type": "cttexpress",
                "product_id": cls.shipping_product.id,
                "debug_logging": True,
                "prod_environment": False,
                # CTT will maintain these credentials in order to allow OCA testing
                "cttexpress_user": "000002ODOO1",
                "cttexpress_password": "CAL%224271",
                "cttexpress_agency": "000002",
                "cttexpress_contract": "1",
                "cttexpress_customer": "ODOO1",
                "cttexpress_shipping_type": "19H",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"type": "consu", "name": "Test product"}
        )
        cls.wh_partner = cls.env["res.partner"].create(
            {
                "name": "My Spanish WH",
                "city": "Zaragoza",
                "zip": "50001",
                "street": "C/ Mayor, 1",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Madrid",
                "zip": "28001",
                "email": "odoo@test.com",
                "street": "Calle de La Rua, 3",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier_cttexpress
        cls.sale_order.action_confirm()
        # Ensure shipper address
        cls.sale_order.warehouse_id.partner_id = cls.wh_partner
        cls.picking = cls.sale_order.picking_ids
        cls.picking.move_lines.quantity_done = 20

    def test_00_cttexpress_test_connection(self):
        """Test credentials validation"""
        self.carrier_cttexpress.action_ctt_validate_user()
        self.carrier_cttexpress.cttexpress_password = "Bad password"
        with self.assertRaises(UserError):
            self.carrier_cttexpress.action_ctt_validate_user()

    def test_01_cttexpress_picking_confirm_simple(self):
        """The picking is confirm and the shipping is recorded to CTT Express"""
        self.picking.button_validate()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.picking.tracking_state_update()
        self.assertTrue(self.picking.tracking_state)
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)

    def test_02_cttexpress_picking_confirm_simple_pt(self):
        """We can deliver from Portugal as well"""
        self.wh_partner.country_id = self.env.ref("base.pt")
        self.picking.button_validate()
        self.assertTrue(self.picking.carrier_tracking_ref)

    def test_03_cttexpress_manifest(self):
        """API work although without data"""
        wizard = self.env["cttexpress.manifest.wizard"].create({})
        wizard.carrier_ids = self.carrier_cttexpress
        wizard.get_manifest()
        # There we have our manifest
        self.assertTrue(wizard.attachment_ids)

    def test_04_cttexpress_pickup(self):
        """API work although without data"""
        wizard = self.env["cttexpress.pickup.wizard"].create(
            {
                "carrier_id": self.carrier_cttexpress.id,
                "min_hour": 0.,
            }
        )
        wizard.create_pickup_request()
        # There we have our manifest
        self.assertTrue(wizard.code)
