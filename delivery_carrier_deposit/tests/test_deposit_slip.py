# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestDepositSlip(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        carrier_id = cls.env.ref("delivery.free_delivery_carrier")
        cls.delivery_order = cls.env.ref("stock.outgoing_shipment_main_warehouse4")
        cls.delivery_order.write({"carrier_id": carrier_id.id})

    def test_delivery_slip_creation(self):
        self.delivery_order.move_line_ids.quantity = 16
        self.delivery_order.button_validate()
        wizard = self.env["delivery.deposit.wizard"].create(
            {
                "delivery_type": "fixed",
            }
        )
        wizard.create_deposit_slip()
        deposit = self.env["deposit.slip"].search([("state", "=", "draft")])
        self.assertEqual(len(deposit), 1)
        self.assertEqual(len(deposit.picking_ids), 1)
        self.assertEqual(deposit.weight, self.delivery_order.shipping_weight)
        deposit.validate_deposit()
        self.assertEqual(deposit.state, "done")
