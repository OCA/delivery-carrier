# Copyright (c) 2026 Groupe Voltaire
# @author Emilie SOUTIRAS <emilie.soutiras@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from unittest import mock

import requests

from odoo.tests.common import Form, TransactionCase

ZPL_PAYLOAD = b"^XA^PW812^LL1218^FO50,50^ADN,36,20^FDHello Voltaire^FS^XZ"
PNG_CONTENT = b"\x89PNG\r\n\x1a\nfake"
REQUESTS_POST = (
    "odoo.addons.delivery_zpl_viewer.wizards.zpl_label_viewer" ".requests.post"
)


class TestZplLabelViewer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        warehouse = cls.env["stock.warehouse"].search([], limit=1)
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.env["res.partner"]
                .create({"name": "ZPL Viewer Test Partner"})
                .id,
                "picking_type_id": warehouse.out_type_id.id,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
            }
        )

    def _attach(self, name, payload=ZPL_PAYLOAD):
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": "stock.picking",
                "res_id": self.picking.id,
                "raw": payload,
            }
        )

    def _open_wizard(self):
        action = self.picking.action_open_zpl_label_viewer()
        return Form(self.env[action["res_model"]].with_context(**action["context"]))

    def _response(self, status=200, content=PNG_CONTENT, headers=None):
        response = mock.Mock(spec=requests.Response)
        response.ok = status == 200
        response.status_code = status
        response.content = content
        response.text = content.decode(errors="ignore")
        response.headers = headers or {}
        return response

    def test_zpl_label_count(self):
        self.assertEqual(self.picking.zpl_label_count, 0)
        self._attach("label.pdf")
        self._attach("CA_PACK0000009.zpl")
        self._attach("CA_PACK0000010.ZPL")
        self.picking.invalidate_recordset(["zpl_label_count"])
        self.assertEqual(self.picking.zpl_label_count, 2)

    def test_wizard_renders_first_label(self):
        first = self._attach("first.zpl")
        self._attach("second.zpl")
        with mock.patch(
            REQUESTS_POST,
            return_value=self._response(headers={"X-Total-Count": "1"}),
        ) as post:
            wizard = self._open_wizard()
        self.assertEqual(wizard.attachment_id, first)
        self.assertEqual(wizard.label_count, 1)
        self.assertEqual(base64.b64decode(wizard.preview_image), PNG_CONTENT)
        self.assertFalse(wizard.preview_error)
        self.assertEqual(
            post.call_args.args[0],
            "https://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/",
        )
        self.assertEqual(post.call_args.kwargs["data"], ZPL_PAYLOAD)

    def test_wizard_uses_default_size_without_zpl_dimensions(self):
        self._attach("label.zpl", b"^XA^FO50,50^FDNo size^FS^XZ")
        self.env["ir.config_parameter"].set_param(
            "delivery_zpl_viewer.default_size", "4x8"
        )
        with mock.patch(REQUESTS_POST, return_value=self._response()) as post:
            self._open_wizard()
        self.assertIn("/labels/4x8/0/", post.call_args.args[0])

    def test_wizard_label_index(self):
        self._attach("label.zpl")
        with mock.patch(
            REQUESTS_POST,
            return_value=self._response(headers={"X-Total-Count": "3"}),
        ) as post:
            wizard = self._open_wizard()
            self.assertEqual(wizard.label_count, 3)
            wizard.label_index = 2
        self.assertTrue(post.call_args.args[0].endswith("/labels/4x6/1/"))

    def test_wizard_labelary_error(self):
        self._attach("label.zpl")
        with mock.patch(
            REQUESTS_POST,
            return_value=self._response(status=400, content=b"ERROR: bad ZPL"),
        ):
            wizard = self._open_wizard()
        self.assertFalse(wizard.preview_image)
        self.assertIn("bad ZPL", wizard.preview_error)

    def test_wizard_labelary_unreachable(self):
        self._attach("label.zpl")
        with mock.patch(
            REQUESTS_POST, side_effect=requests.ConnectionError("no route")
        ):
            wizard = self._open_wizard()
        self.assertFalse(wizard.preview_image)
        self.assertIn("no route", wizard.preview_error)
