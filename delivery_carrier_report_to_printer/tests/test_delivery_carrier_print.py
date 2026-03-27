# Copyright 2025 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestCarrierPrint(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_type = cls.env.ref("stock.picking_type_out")
        cls.report = cls.env.ref(
            "delivery_carrier_report_to_printer.report_carrier_label"
        )
        cls.picking_type.print_label = True
        cls.server = cls.env["printing.server"].create({})
        cls.printer = cls.env["printing.printer"].create(
            {
                "name": "Test printer",
                "server_id": cls.server.id,
                "system_name": "Test printer",
                "status": "available",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "is_storable": True}
        )
        cls.delivery_product = cls.env["product.product"].create(
            {"name": "Test product", "type": "service"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "test123",
                "delivery_type": "fixed",
                "integration_level": "rate_and_ship",
                "product_id": cls.delivery_product.id,
                "label_report_id": cls.report.id,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.picking_type.default_location_src_id, 1
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.picking_type.id,
                "partner_id": cls.partner.id,
                "carrier_id": cls.carrier.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "name": cls.product.display_name,
                            "quantity": 1,
                            "picked": True,
                            "location_id": cls.picking_type.default_location_src_id.id,
                            "location_dest_id": cls.partner.property_stock_customer.id,
                        },
                    )
                ],
            }
        )

    def fake_fixed_send_shipping(self, pickings, *args, **kwargs):
        # Simulate a shipping label being generated
        self.env["ir.attachment"].create(
            {
                "name": "label_TEST123456.pdf",
                "datas": "JVBERi0xLjQKJcfs",
                "mimetype": "application/pdf",
                "res_model": pickings._name,
                "res_id": pickings.id,
            }
        )
        return [
            {
                "exact_price": pickings.carrier_id.fixed_price,
                "tracking_number": "TEST123456",
            }
        ]

    def test_no_report(self):
        self.carrier.label_report_id = False
        self.assertEqual(self.picking.message_attachment_count, 0)
        with patch(
            "odoo.addons.stock_delivery.models.delivery_carrier.DeliveryCarrier.fixed_send_shipping",
        ) as mocked_session:
            mocked_session.side_effect = self.fake_fixed_send_shipping
            self.picking._action_done()
        self.picking.invalidate_recordset(["message_attachment_count"])
        self.assertEqual(self.picking.message_attachment_count, 1)
        self.assertEqual(len(self.printer.job_ids), 0)

    def test_print_label_to_client(self):
        self.env.user.printing_action = "client"
        self.assertEqual(self.picking.message_attachment_count, 0)
        with patch(
            "odoo.addons.stock_delivery.models.delivery_carrier.DeliveryCarrier.fixed_send_shipping",
        ) as mocked_session:
            mocked_session.side_effect = self.fake_fixed_send_shipping
            self.picking._action_done()
        self.picking.invalidate_recordset(["message_attachment_count"])
        self.assertEqual(self.picking.message_attachment_count, 1)
        self.assertEqual(len(self.printer.job_ids), 0)

    @mute_logger("odoo.addons.base_report_to_printer.models.printing_server")
    def test_print_label_to_server(self):
        self.report.printing_printer_id = self.printer
        self.report.property_printing_action_id = False  # Reset to use user default
        self.env.user.printing_action = "server"
        self.assertEqual(self.picking.message_attachment_count, 0)
        with patch(
            "odoo.addons.stock_delivery.models.delivery_carrier.DeliveryCarrier.fixed_send_shipping",
        ) as mocked_session:
            mocked_session.side_effect = self.fake_fixed_send_shipping
            # the printing fails due to no CUPS server being available
            with self.assertRaisesRegex(
                UserError, "Failed to connect to the CUPS server"
            ):
                self.picking._action_done()
        self.picking.invalidate_recordset(["message_attachment_count"])
        self.assertEqual(self.picking.message_attachment_count, 1)
