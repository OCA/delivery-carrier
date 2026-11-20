# Copyright 2020 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from unittest.mock import call, patch

from lxml import html

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import Form
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryPackageNumber(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "consu", "is_storable": True}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.wh1 = cls.env["stock.warehouse"].create(
            {"name": "TEST WH1", "code": "TST1"}
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "location_id": cls.wh1.lot_stock_id.id,
                "location_dest_id": cls.wh1.wh_output_stock_loc_id.id,
                "picking_type_id": cls.wh1.int_type_id.id,
            }
        )
        cls.move_line_obj = cls.env["stock.move.line"]
        cls.ml1 = cls.move_line_obj.create(
            {
                "product_id": cls.product.id,
                "uom_id": cls.product.uom_id.id,
                "quantity": 5,
                "location_id": cls.wh1.lot_stock_id.id,
                "location_dest_id": cls.wh1.wh_output_stock_loc_id.id,
                "picking_id": cls.picking.id,
            }
        )
        cls.ml2 = cls.ml1.copy({"quantity": 0})

    def test_number_of_packages(self):
        # By default it's computed to 0
        self.assertEqual(self.picking.number_of_packages, 0)
        # We can edit the number of packages as there aren't delivery packages
        picking_form = Form(self.picking)
        picking_form.number_of_packages = 3
        picking_form.save()
        self.assertEqual(self.picking.number_of_packages, 3)
        # We add a package and it recalculates
        self.picking.action_put_in_pack()
        self.assertEqual(self.picking.number_of_packages, 1)
        self.ml2.quantity = 5
        self.picking.action_put_in_pack()
        self.assertEqual(self.picking.number_of_packages, 2)
        # Several lines in the same package must only count once.
        self.ml1.copy({"quantity": 1})
        self.assertEqual(self.picking.number_of_packages, 2)
        # We can later set it manually if we want to
        picking_form.number_of_packages = 3
        picking_form.save()
        self.assertEqual(self.picking.number_of_packages, 3)

    def test_backorder(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 10
        order = order_form.save()
        order.action_confirm()
        picking = order.picking_ids
        picking.move_ids.quantity = 2
        picking.number_of_packages = 2
        action = picking.with_context(
            test_delivery_package_number=True
        ).button_validate()
        backorder_wizard = Form(
            self.env[action["res_model"]].with_context(**action["context"])
        ).save()
        backorder_wizard.process()
        done_picking = order.picking_ids.filtered(lambda x: x.state == "done")
        new_picking = order.picking_ids - done_picking
        self.assertEqual(done_picking.number_of_packages, 2)
        self.assertEqual(new_picking.number_of_packages, 0)

    def _create_delivery(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    fields.Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                        }
                    )
                ],
            }
        )
        order.action_confirm()
        picking = order.picking_ids
        picking.move_ids.quantity = 1
        picking.picking_type_id.write(
            {
                "force_set_number_of_packages": True,
                "avoid_set_number_of_packages": False,
                "print_label": False,
            }
        )
        return picking.with_context(test_delivery_package_number=True)

    def _open_package_wizard(self, pickings):
        action = pickings.button_validate()
        self.assertEqual(action["res_model"], "stock.number.package.validate.wizard")
        return Form(
            pickings.env[action["res_model"]].with_context(**action["context"])
        ).save()

    def test_package_wizard_validate_once(self):
        picking = self._create_delivery()
        wizard = self._open_package_wizard(picking)
        self.assertEqual(wizard.pick_ids, picking)
        self.assertFalse(wizard.print_package_label)
        wizard.number_of_packages = 3
        wizard.process()
        self.assertEqual(picking.number_of_packages, 3)
        self.assertEqual(picking.state, "done")
        self.assertIs(picking.button_validate(), True)

    def test_package_wizard_carrier(self):
        picking = self._create_delivery()
        picking.picking_type_id.force_set_number_of_packages = False
        picking.carrier_id = self.env["delivery.carrier"].create(
            {
                "name": "Test fixed carrier",
                "delivery_type": "fixed",
                "product_id": self.product.id,
                "integration_level": "rate",
            }
        )
        wizard = self._open_package_wizard(picking)
        wizard.number_of_packages = 3
        wizard.process()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.number_of_packages, 3)

    def test_package_wizard_conditions(self):
        for force, avoid, number, expected in [
            (False, False, 0, False),
            (True, False, 0, True),
            (False, True, 0, False),
            (True, True, 0, False),
            (True, False, 3, False),
        ]:
            with self.subTest(force=force, avoid=avoid, number=number):
                picking = self._create_delivery()
                picking.picking_type_id.write(
                    {
                        "force_set_number_of_packages": force,
                        "avoid_set_number_of_packages": avoid,
                    }
                )
                picking.number_of_packages = number
                action = picking.button_validate()
                if expected:
                    self.assertEqual(
                        action["res_model"], "stock.number.package.validate.wizard"
                    )
                    self.assertNotEqual(picking.state, "done")
                else:
                    self.assertIs(action, True)
                    self.assertEqual(picking.state, "done")
                    self.assertEqual(picking.number_of_packages, number)

    def test_package_wizard_multiple_pickings(self):
        pickings = self._create_delivery() | self._create_delivery()
        wizard = self._open_package_wizard(pickings)
        lines = wizard.stock_number_package_validation_line_ids
        self.assertEqual(lines.picking_id, pickings)
        for line, number in zip(lines, (2, 3), strict=True):
            line.number_of_packages = number
        wizard.process()
        self.assertEqual(pickings.mapped("number_of_packages"), [2, 3])
        self.assertEqual(pickings.mapped("state"), ["done", "done"])

    def test_package_label_report(self):
        # Configure the company layout so printing returns the report action,
        # rather than the first-time document layout configuration wizard.
        self.env.company.external_report_layout_id = self.env.ref(
            "web.external_layout_standard"
        )
        picking = self._create_delivery()
        picking.picking_type_id.print_label = True
        report = self.env.ref(
            "delivery_package_number.action_delivery_package_number_report"
        ).copy({"name": "Selected package report"})
        picking.picking_type_id.report_number_of_packages = report
        wizard = self._open_package_wizard(picking)
        self.assertTrue(wizard.print_package_label)
        wizard.number_of_packages = 3
        action = wizard.process()
        self.assertEqual(picking.state, "done")
        self.assertEqual(action["report_name"], report.report_name)
        self.assertEqual(action["name"], report.name)
        self.assertTrue(action["close_on_report_download"])
        # Keep QWeb real, but isolate ReportLab's native raster backend.
        # A valid 1x1 PNG is enough to check the barcode image embedding.
        barcode_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
            "/x8AAwMCAO+aD1sAAAAASUVORK5CYII="
        )
        with patch.object(type(report), "barcode", return_value=barcode_png) as barcode:
            content, _ = report._render_qweb_html(report.report_name, picking.ids)
        self.assertEqual(barcode.call_args_list, [call("Code128", picking.name)] * 3)
        document = html.fromstring(content)
        pages = document.xpath("//div[@class='page']")
        self.assertEqual(len(pages), 3)
        for number, page in enumerate(pages, 1):
            label = page.xpath(".//div[@name='package_number']")[0]
            label_text = "".join("".join(label.itertext()).split())
            self.assertIn(f"{number}/3", label_text)
            self.assertIn(self.partner.name, page.text_content())
            self.assertIn(picking.name, page.text_content())
            self.assertTrue(page.xpath(".//div[@name='picking_ref']//img"))

    def test_package_wizard_stock_user_company(self):
        picking = self._create_delivery()
        user = new_test_user(
            self.env,
            login="package_stock_user",
            groups="stock.group_stock_user",
            company_id=self.env.company.id,
            company_ids=[fields.Command.set(self.env.company.ids)],
        )
        other_company = self.env["res.company"].create({"name": "Other company"})
        other_warehouse = self.env["stock.warehouse"].create(
            {"name": "Other WH", "code": "OTH", "company_id": other_company.id}
        )
        other_picking = self.env["stock.picking"].create(
            {
                "company_id": other_company.id,
                "picking_type_id": other_warehouse.out_type_id.id,
                "location_id": other_warehouse.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            }
        )
        wizard = self._open_package_wizard(picking.with_user(user))
        wizard.number_of_packages = 3
        wizard.process()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.number_of_packages, 3)
        with self.assertRaises(AccessError):
            other_picking.with_user(user).read(["number_of_packages"])
