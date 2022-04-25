# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class DeliveryUps(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_shipping_cost = cls.env["product.product"].create(
            {
                "type": "service",
                "name": "Shipping costs",
                "standard_price": 10,
                "list_price": 100,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "UPS",
                "delivery_type": "ups",
                "product_id": product_shipping_cost.id,
                "price_method": "fixed",
                "ups_default_packaging_id": cls.env.ref(
                    "delivery_ups_oca.product_packaging_ups_02"
                ).id,
                #
                # This account was issued by Odoo S.A. and we are borrowing it
                # from data seen on enterprise runbot.
                #
                "ups_ws_username": "ups_odoo_test",
                "ups_ws_password": "Zh7~Q-bk/R7CeCxQS}Iw",
                "ups_access_license": "ED7F8A752151DEF5",
                "ups_shipper_number": "R5R012",
                "ups_service_code": "02",
                "debug_logging": True,
                "prod_environment": False,
            }
        )
        cls.company = cls.env.ref("base.main_company")
        cls.company.partner_id.write(
            {
                "phone": "+%s976123456" % cls.company.country_id.phone_code,
                "vat": "%s09915370R" % cls.company.country_id.code,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "country_id": cls.company.country_id.id,
                "phone": cls.company.partner_id.phone,
                "email": "test@odoo.com",
                "street": cls.company.partner_id.street,
                "city": cls.company.partner_id.city,
                "zip": cls.company.partner_id.zip,
                "state_id": cls.company.partner_id.state_id.id,
                "vat": cls.company.partner_id.vat,
            }
        )
        cls.product = cls.env.ref("product.product_delivery_01")
        cls.product.write({"weight": 10})
        cls.sale = cls._create_sale_order(cls)
        cls.picking = cls.sale.picking_ids[0]
        cls.picking.move_lines.quantity_done = 10
        # We make a test call to avoid errors in tests
        response = cls.carrier.ups_test_call(cls.sale)
        cls.ups_ws_status = True if not response["errors"] else False

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 10
        sale = order_form.save()
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": sale.id, "default_carrier_id": self.carrier.id}
            )
        ).save()
        delivery_wizard.button_confirm()
        sale.action_confirm()
        return sale

    def test_order_ups_rate_shipment(self):
        if not self.ups_ws_status:
            self.skipTest("UPS webservice with errors")
        res = self.carrier.ups_rate_shipment(self.sale)
        self.assertGreater(res["price"], 0)
        self.assertTrue(res["success"])

    def test_order_ups_rate_shipment_currency_extra(self):
        if not self.ups_ws_status:
            self.skipTest("UPS webservice with errors")
        usd = self.env.ref("base.USD")
        eur = self.env.ref("base.EUR")
        currency = self.env.ref("base.main_company").currency_id
        currency_extra = eur if currency == usd else usd
        self.sale.currency_id = currency_extra
        res = self.carrier.ups_rate_shipment(self.sale)
        self.assertGreater(res["price"], 0)
        self.assertTrue(res["success"])

    def test_delivery_carrier_ups_integration(self):
        if not self.ups_ws_status:
            self.skipTest("UPS webservice with errors")
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.send_to_shipper()
        self.assertEquals(self.picking.message_attachment_count, 1)
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.tracking_state_history)
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        if self.picking.carrier_id.ups_tracking_state_update_sync:
            self.picking.tracking_state_update()
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")
