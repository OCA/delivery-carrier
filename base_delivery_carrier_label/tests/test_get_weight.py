# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase
from odoo.tools import float_compare


class TestGetWeight(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.g_product = cls.env["product.product"].create(
            {
                "name": "Product in g",
                "type": "consu",
                "uom_id": cls.env.ref("uom.product_uom_gram").id,
                "uom_po_id": cls.env.ref("uom.product_uom_gram").id,
            }
        )
        cls.kg_product = cls.env["product.product"].create(
            {
                "name": "Product in kg",
                "type": "consu",
                "uom_id": cls.env.ref("uom.product_uom_kgm").id,
                "uom_po_id": cls.env.ref("uom.product_uom_kgm").id,
            }
        )
        cls.unit_product = cls.env["product.product"].create(
            {
                "name": "Product in piece",
                "type": "consu",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "uom_po_id": cls.env.ref("uom.product_uom_unit").id,
                "weight": 2.2,
            }
        )
        cls.liter_product = cls.env["product.product"].create(
            {
                "name": "Olive oil in L",
                "type": "consu",
                "uom_id": cls.env.ref("uom.product_uom_litre").id,
                "uom_po_id": cls.env.ref("uom.product_uom_litre").id,
                "weight": 0.92,
            }
        )
        cls.company = cls.env.ref("base.main_company")
        cls.wh = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        # set reference uom as kg and not pound
        cls.env["ir.config_parameter"].set_param("product.weight_in_lbs", "0")

    def test_weight(self):
        picking = self.env["stock.picking"].create(
            {
                "company_id": self.company.id,
                "picking_type_id": self.wh.out_type_id.id,
                "location_id": self.wh.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.g_product.id,
                            "product_uom": self.g_product.uom_id.id,
                            "name": self.g_product.display_name,
                            "product_uom_qty": 600,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.kg_product.id,
                            "product_uom": self.kg_product.uom_id.id,
                            "name": self.kg_product.display_name,
                            "product_uom_qty": 3.5,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.unit_product.id,
                            "product_uom": self.unit_product.uom_id.id,
                            "name": self.unit_product.display_name,
                            "product_uom_qty": 4,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.liter_product.id,
                            "product_uom": self.liter_product.uom_id.id,
                            "name": self.liter_product.display_name,
                            "product_uom_qty": 2,
                        },
                    ),
                ],
            }
        )
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        result = {
            self.g_product: 0.6,
            self.kg_product: 3.5,
            self.unit_product: 2.2 * 4,
            self.liter_product: 0.92 * 2,
        }
        wprec = self.env["decimal.precision"].precision_get("Stock Weight")
        for move_line in picking.move_line_ids:
            move_line.write({"qty_done": move_line.product_uom_qty})
            self.assertFalse(
                float_compare(
                    move_line.get_weight(),
                    result[move_line.product_id],
                    precision_digits=wprec,
                )
            )
        picking.action_put_in_pack()
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        package = picking.move_line_ids[0].result_package_id
        self.assertFalse(
            float_compare(package.weight, sum(result.values()), precision_digits=wprec)
        )
