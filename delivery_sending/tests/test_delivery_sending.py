# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class TestDeliverySendingBase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_sc = cls.env["product.product"].create(
            {"type": "service", "name": "Shipping costs"}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Sending",
                "delivery_type": "sending",
                "product_id": product_sc.id,
                "sending_user": "sending_odoo_test",
                "sending_access_key": "odoo",
                "sending_service": "01",
                "debug_logging": True,
                "prod_environment": False,
            }
        )
        cls.company = cls.env.ref("base.main_company")
        country_es = cls.env.ref("base.es")
        cls.company.write(
            {
                "country_id": country_es.id,
                "state_id": cls.env.ref("base.state_es_m").id,
                "city": "Madrid",
                "zip": "28231",
                "street": "Calle falsa 12",
                "phone": "+%s976123456" % country_es.phone_code,
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
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product", "weight": 1}
        )
        cls.sale = cls._create_sale_order(cls)

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
        sale = order_form.save()
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": sale.id, "default_carrier_id": self.carrier.id}
            )
        ).save()
        delivery_wizard.button_confirm()
        sale.action_confirm()
        return sale


class TestDeliverySending(TestDeliverySendingBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = cls.sale.picking_ids[0]
        cls.picking.move_lines.quantity_done = 10

    def test_order_sending_rate_shipment_error(self):
        with self.assertRaises(NotImplementedError):
            self.carrier.sending_rate_shipment(self.sale)

    def test_delivery_carrier_sending_integration(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        # We need to send a context to avoid a bug with the api because there is no
        # test user.
        # We simulate the complete flow to test all carrier methods.
        self.picking.with_context(skip_errors=True).send_to_shipper()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.tracking_state_history)
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        self.picking.with_context(skip_errors=True).cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")
