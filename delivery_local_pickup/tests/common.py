# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class DeliveryLocalPickupCommon(common.SavepointCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.company.write(
            {
                "stock_move_email_validation": True,
                "stock_mail_confirmation_template_id": self.env.ref(
                    "stock.mail_template_data_delivery_confirmation"
                ).id,
            }
        )
        product_shipping_cost = self.env["product.product"].create(
            {"type": "service", "name": "Shipping costs"}
        )
        address = self.env["res.partner"].create(
            {
                "name": "Local address partner",
                "country_id": self.company.country_id.id,
                "phone": self.company.partner_id.phone,
                "email": "test@odoo.com",
                "street": self.company.partner_id.street,
                "city": self.company.partner_id.city,
                "zip": self.company.partner_id.zip,
                "state_id": self.company.partner_id.state_id.id,
            }
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Local pickup",
                "delivery_type": "local_pickup",
                "product_id": product_shipping_cost.id,
                "local_address_id": address.id,
            }
        )
        self.partner = self.env["res.partner"].create(
            {"name": "Mr partner", "email": "mr@odoo.com"}
        )
        self.product = self.env.ref("product.product_delivery_01")
        self.sale = self._create_sale_order()
        self.picking = self.sale.picking_ids[0]
        self.picking.move_lines.quantity_done = 10

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
