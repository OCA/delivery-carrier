# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import Form, SavepointCase
from odoo.tools import mute_logger


class TestPackageFee(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.product1 = cls.env["product.product"].create(
            {"name": "Product 1", "type": "product", "lst_price": 1.0}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})
        product_delivery = cls.env["product.product"].create(
            {"name": "Delivery Product", "type": "service"}
        )
        cls.carrier1 = cls.env["delivery.carrier"].create(
            {
                "name": "Delivery 1",
                "fixed_price": 10.0,
                "product_id": product_delivery.id,
            }
        )
        cls.sale = cls._create_sale()

    @classmethod
    def _create_sale(cls):
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with mute_logger("odoo.tests.common.onchange"):
            with sale_form.order_line.new() as line:
                line.product_id = cls.product1
                line.product_uom_qty = 10.0
        return sale_form.save()

    def test_delivery_carrier_constrained(self):
        # cannot call wizard if carrier set
        self.sale.order_line[0].write({"carrier_id": self.carrier1.id})
        with self.assertRaises(UserError):
            self.sale.action_open_delivery_wizard()
