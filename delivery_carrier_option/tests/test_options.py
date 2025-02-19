# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestPickingOption(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier = cls.env.ref("delivery.delivery_carrier")
        cls.option1 = cls.env["delivery.carrier.option"].create(
            {
                "name": "Option1",
                "code": "Code 1",
                "carrier_id": cls.carrier.id,
            }
        )
        cls.option2 = cls.env["delivery.carrier.option"].create(
            {
                "name": "Option2",
                "code": "Code 2",
                "carrier_id": cls.carrier.id,
            }
        )
        cls.option3 = cls.env["delivery.carrier.option"].create(
            {
                "name": "Option3",
                "code": "Code 3",
                "carrier_id": cls.carrier.id,
                "by_default": True,
            }
        )

    def test_delivery_carrier_option_color(self):
        self.assertFalse(self.option1.color)
        self.option1.mandatory = True
        self.assertEqual(self.option1.color, 2)

    def test_picking_default_options(self):
        self.option1.mandatory = True
        picking = self.env["stock.picking"].create(
            {
                "carrier_id": self.carrier.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )
        self.assertIn(self.option1, picking.option_ids)
        self.assertNotIn(self.option2, picking.option_ids)
        self.assertIn(self.option3, picking.option_ids)
