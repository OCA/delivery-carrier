# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form, common


class DeliveryGefco(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        partner_gefco = cls.env["res.partner"].create({"name": "Mr Gefco"})
        product_gefco = cls.env["product.product"].create(
            {"name": "Gefco", "type": "service"}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Gefco",
                "delivery_type": "gefco",
                "partner_id": partner_gefco.id,
                "gefco_agency_code": "AGENCY-CODE",
                "gefco_shipper_id": "SHIPPER-ID",
                "product_id": product_gefco.id,
            }
        )
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "country_id": cls.company.partner_id.country_id.id,
                "phone": cls.company.partner_id.phone,
                "email": "test@odoo.com",
                "street": cls.company.partner_id.street,
                "city": cls.company.partner_id.city,
                "zip": cls.company.partner_id.zip,
                "state_id": cls.company.partner_id.state_id.id,
                "vat": cls.company.partner_id.vat,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product"}
        )
        cls.sale = cls._create_sale_order(cls)
        cls.picking = cls.sale.picking_ids[0]
        cls.picking.move_lines.quantity_done = 1

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

    def _create_gefco_destination(self):
        self.env["gefco.destination"].create(
            {
                "country_code": self.partner.country_id.code,
                "zip_code": self.partner.zip,
                "directional_code": "CODE",
            }
        )

    def test_order_gefco_rate_shipment(self):
        with self.assertRaises(NotImplementedError):
            self.carrier.gefco_rate_shipment(self.sale)

    def test_delivery_carrier_gefco_zpl_error_carrier_tracking_ref(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        with self.assertRaises(UserError):
            self.picking.send_to_shipper()

    def test_delivery_carrier_gefco_zpl_error_gefco_festination_id(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.carrier_tracking_ref = "CUSTOM_REF"
        with self.assertRaises(UserError):
            self.picking.send_to_shipper()

    def test_delivery_carrier_gefco_zpl(self):
        self._create_gefco_destination()
        # Force compute gefco_destination_id again to prevent error
        self.picking._compute_gefco_destination_id()
        self.picking.carrier_tracking_ref = "CUSTOM_REF"
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.send_to_shipper()
        self.assertEquals(self.picking.message_attachment_count, 1)
        self.assertTrue(self.picking.gefco_destination_id)
        with self.assertRaises(NotImplementedError):
            self.picking.cancel_shipment()
