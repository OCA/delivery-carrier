# Copyright 2023 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, SavepointCase


class TestDeliveryCarrierTypology(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.delivery_carrier = cls.env.ref("delivery.delivery_carrier")
        air_freight = cls.env["delivery.carrier.typology"].create(
            {"name": "Air freight"}
        )
        sea_freight = cls.env["delivery.carrier.typology"].create(
            {"name": "Sea freight"}
        )
        cls.delivery_carrier.write(
            {"shipping_means_ids": [(6, 0, [air_freight.id, sea_freight.id])]}
        )
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.product = cls.env.ref("product.product_product_6")
        cls.product.write({"prohibited_shipping_means_ids": [(6, 0, air_freight.ids)]})

    def test_available_carrier(self):
        sale_order = self._create_sale_order(self.partner, self.product)
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "active_model": "sale.order",
                    "active_id": sale_order.id,
                    "default_order_id": sale_order.id,
                    "default_carrier_id": self.delivery_carrier.id,
                }
            )
        )
        self.assertTrue(
            self.delivery_carrier not in set(delivery_wizard.available_carrier_ids)
        )

    def _create_sale_order(self, partner, product):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = product
        return order_form.save()
