# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import base64

from odoo.addons.base.tests.common import BaseCommon

from .common import HTMLRenderMixin


class TestPrintLabel(BaseCommon, HTMLRenderMixin):
    """Test label printing.

    When running tests Odoo renders PDF reports as HTML,
    so we are going to test the shipping labels as HTML document only.
    A good side effect: we are able to test the rendered content.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        Product = cls.env["product.product"]
        Picking = cls.env["stock.picking"]
        Move = cls.env["stock.move"]
        Carrier = cls.env["delivery.carrier"]
        ShippingLabel = cls.env["shipping.label"]

        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

        cls.new_carrier_product = Product.create(
            {
                "name": "Test NEW carrier product",
                "type": "service",
            }
        )
        cls.new_carrier = Carrier.create(
            {
                "name": "Test NEW carrier",
                "delivery_type": "fixed",
                "product_id": cls.new_carrier_product.id,
            }
        )

        cls.picking = Picking.create(
            {
                "partner_id": cls.env.ref("base.res_partner_12").id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "carrier_id": cls.new_carrier.id,
            }
        )
        cls.product_a = Product.create({"name": "Product A"})
        cls.product_b = Product.create({"name": "Product B"})

        cls.move1 = Move.create(
            {
                "name": "Move A",
                "picking_id": cls.picking.id,
                "product_id": cls.product_a.id,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "product_uom_qty": 3.0,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

        cls.move2 = Move.create(
            {
                "name": "a second move",
                "product_id": cls.product_b.id,
                "product_uom_qty": 12.0,
                "product_uom": cls.product_b.uom_id.id,
                "picking_id": cls.picking.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )

        cls.picking.action_confirm()
        cls.picking.action_assign()

        cls.move1.move_line_ids[0].write({"quantity": 2, "picked": True})
        cls.move2.move_line_ids[0].write({"quantity": 2, "picked": True})

        cls.picking.action_put_in_pack()

        cls.label = cls.picking.generate_default_label()
        cls.shipping_label_1 = ShippingLabel.create(
            {
                "name": cls.label["name"],
                "res_id": cls.picking.id,
                "package_id": cls.move1.move_line_ids[0].result_package_id.id,
                "res_model": "stock.picking",
                "datas": cls.label["file"],
                "file_type": cls.label["file_type"],
            }
        )

    def check_label_content(self, b64_datas):
        html_datas = base64.b64decode(b64_datas)
        node = self.to_xml_node(html_datas)[0]
        for div_class in ["page", "address", "recipient"]:
            tags = self.find_div_class(node, div_class)
            self.assertEqual(len(tags), 1)

    # @patch_label_file_type
    def test_001_print_default_label(self):
        # assign picking to generate 'stock.move.line'
        self.picking.send_to_shipper()
        label = self.env["shipping.label"].search([("res_id", "=", self.picking.id)])
        self.assertEqual(len(label), 1)
        self.assertTrue(label.datas)
        self.assertEqual(label.name, "Shipping Label.html")
        self.assertEqual(label.file_type, "html")
        self.check_label_content(label.datas)

    # @patch_label_file_type
    def test_002_print_default_label_selected_packs(self):
        # create packs
        self.move1.move_line_ids[0].write({"quantity": 3, "picked": True})
        self.move2.move_line_ids[0].write({"quantity": 3, "picked": True})
        self.picking.action_put_in_pack()
        for ope in self.picking.move_line_ids:
            if ope.quantity == 0:
                ope.quantity = 9
                break
        self.picking.action_put_in_pack()
        self.picking.send_to_shipper()
        labels = self.env["shipping.label"].search([("res_id", "=", self.picking.id)])
        self.assertEqual(len(labels), 1)
        for label in labels:
            self.assertTrue(label.datas)
            self.assertEqual(label.name, "Shipping Label.html")
            self.assertEqual(label.file_type, "html")
            self.check_label_content(label.datas)
