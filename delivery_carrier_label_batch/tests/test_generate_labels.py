# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import base64

import odoo.tests.common as common
from odoo import exceptions
from odoo.modules import get_module_resource


class TestGenerateLabels(common.SavepointCase):

    """Test the wizard for delivery carrier label generation"""

    @classmethod
    def setUpClass(cls):
        super(TestGenerateLabels, cls).setUpClass()

        Move = cls.env["stock.move"]
        Picking = cls.env["stock.picking"]
        ShippingLabel = cls.env["shipping.label"]
        BatchPicking = cls.env["stock.picking.batch"]
        cls.DeliveryCarrierLabelGenerate = cls.env["delivery.carrier.label.generate"]
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

        cls.productA = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.productB = cls.env["product.product"].create(
            {"name": "Product B", "type": "product"}
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.productA, cls.stock_location, 20.0
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.productB, cls.stock_location, 20.0
        )

        picking_out_1 = Picking.create(
            {
                "partner_id": cls.env.ref("base.res_partner_12").id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
            }
        )

        picking_out_2 = Picking.create(
            {
                "partner_id": cls.env.ref("base.res_partner_12").id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
            }
        )

        move1 = Move.create(
            {
                "name": "/",
                "picking_id": picking_out_1.id,
                "product_id": cls.productA.id,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "product_uom_qty": 2,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

        move2 = Move.create(
            {
                "name": "/",
                "picking_id": picking_out_2.id,
                "product_id": cls.productB.id,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "product_uom_qty": 1,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

        cls.batch = BatchPicking.create(
            {
                "name": "demo_prep001",
                "picking_ids": [(4, picking_out_1.id), (4, picking_out_2.id)],
                "use_oca_batch_validation": True,
            }
        )

        cls.batch.action_confirm()
        cls.batch.action_assign()

        move1.move_line_ids[0].qty_done = 2
        move2.move_line_ids[0].qty_done = 2

        picking_out_1.action_put_in_pack()
        picking_out_2.action_put_in_pack()

        label = ""
        dummy_pdf_path = get_module_resource(
            "delivery_carrier_label_batch", "tests", "dummy.pdf"
        )
        with open(dummy_pdf_path, "rb") as dummy_pdf:
            label = dummy_pdf.read()

        ShippingLabel.create(
            {
                "name": "picking_out_1",
                "res_id": picking_out_1.id,
                "package_id": move1.move_line_ids[0].result_package_id.id,
                "res_model": "stock.picking",
                "datas": base64.b64encode(label),
                "file_type": "pdf",
            }
        )

        ShippingLabel.create(
            {
                "name": "picking_out_2",
                "res_id": picking_out_2.id,
                "package_id": move2.move_line_ids[0].result_package_id.id,
                "res_model": "stock.picking",
                "datas": base64.b64encode(label),
                "file_type": "pdf",
            }
        )

    def test_action_generate_labels(self):
        """Check merging of pdf labels

        Test pdf generation without multiple threading

        """
        wizard = self.DeliveryCarrierLabelGenerate.with_context(
            active_ids=self.batch.ids, active_model="stock.picking.batch"
        ).create({"generate_new_labels": True})

        wizard.action_generate_labels()

        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "stock.picking.batch"), ("res_id", "=", self.batch.id)]
        )

        self.assertEqual(len(attachment), 1)
        self.assertTrue(attachment.datas)
        self.assertTrue(attachment.name, "demo_prep001.pdf")
        self.assertTrue(attachment.mimetype, "application/pdf")

    def test_action_generate_labels_no_pack(self):
        """Check merging of pdf labels

        It shouldn't be possible to print labels when packages are missing
        """
        domain = [("picking_id", "in", self.batch.picking_ids.ids)]
        self.env["stock.package_level"].search(domain).unlink()
        wizard = self.DeliveryCarrierLabelGenerate.with_context(
            active_ids=self.batch.ids, active_model="stock.picking.batch"
        ).create({})
        with self.assertRaises(exceptions.UserError):
            wizard.action_generate_labels()
