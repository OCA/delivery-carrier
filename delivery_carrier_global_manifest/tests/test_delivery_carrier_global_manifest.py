# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import exceptions
from odoo.tests.common import Form, TransactionCase


class TestDeliveryCarrierGlobalManifest(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.pick_type_out = cls.env.ref("stock.picking_type_out")
        cls.carrier = cls.env.ref("delivery.delivery_carrier")
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "detailed_type": "product"}
        )
        cls.wh = cls.env["stock.warehouse"].create({"name": "TEST WH", "code": "TST1"})
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "carrier_id": cls.carrier.id,
                "picking_type_id": cls.pick_type_out.id,
                "company_id": cls.env.user.company_id.id,
                "location_id": cls.wh.lot_stock_id.id,
                "location_dest_id": cls.wh.wh_output_stock_loc_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Move",
                            "product_id": cls.product.id,
                            "product_uom": cls.product.uom_id.id,
                            "product_uom_qty": 1,
                            "quantity": 1,
                            "location_id": cls.wh.lot_stock_id.id,
                            "location_dest_id": cls.wh.wh_output_stock_loc_id.id,
                        },
                    )
                ],
            }
        )

    def test_delivery_carrier_global_manifest(self):
        self.picking.action_confirm()
        self.picking.button_validate()
        wizard = self.env["manifest.wizard"].create(
            {"global_manifest_query": True, "from_date": datetime.date.today()}
        )
        pickings = wizard._get_global_manifest_pickings()
        self.assertEqual(pickings, self.picking)
        wizard.get_manifest_file()
        self.assertEqual(wizard.state, "file")
        self.assertTrue(wizard.file_out)

    def test_no_deliveries(self):
        wizard = self.env["manifest.wizard"].create(
            {"global_manifest_query": True, "from_date": datetime.date.today()}
        )
        with self.assertRaises(exceptions.ValidationError):
            wizard.get_manifest_file()

    def test_multicompany(self):
        company_1 = self.env.ref("base.main_company")
        company_2 = self.env.ref("stock.res_company_1")

        carrier_global = self.env.ref("delivery.free_delivery_carrier")
        carrier_c1 = self.env.ref("delivery.delivery_carrier")
        carrier_c1.company_id = company_1
        carrier_c2 = self.env.ref("delivery.delivery_local_delivery")
        carrier_c2.company_id = company_2

        wizard = self.env["manifest.wizard"].create(
            {"global_manifest_query": True, "from_date": datetime.date.today()}
        )
        self.assertTrue(carrier_global <= wizard.global_carrier_ids)

        with Form(wizard) as wiz_form:
            wiz_form.company_id = company_1
            wizard = wiz_form.save()
        self.assertTrue(carrier_global + carrier_c1 <= wizard.global_carrier_ids)

        with Form(wizard) as wiz_form:
            wiz_form.company_id = company_2
            wizard = wiz_form.save()
        self.assertTrue(carrier_global + carrier_c2 <= wizard.global_carrier_ids)
