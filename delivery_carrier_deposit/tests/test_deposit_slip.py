# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo_test_helper import FakeModelLoader

from odoo.tests.common import SavepointCase


class TestDepositSlip(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        # The fake class is imported here !! After the backup_registry
        from .models import FakeDeliveryCarrier

        cls.loader.update_registry((FakeDeliveryCarrier,))

        delivery_free_product = cls.env.ref("delivery.product_product_delivery")
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "test",
                "product_id": delivery_free_product.id,
            }
        )
        cls.delivery_order = cls.env.ref("stock.outgoing_shipment_main_warehouse4")
        cls.delivery_order.write({"carrier_id": cls.carrier.id})

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_delivery_slip_creation(self):
        self.delivery_order._action_done()
        wizard = self.env["delivery.deposit.wizard"].create(
            {
                "delivery_type": "test",
            }
        )
        wizard.create_deposit_slip()
        deposit = self.env["deposit.slip"].search([("state", "=", "draft")])
        self.assertEqual(len(deposit), 1)
        self.assertEqual(len(deposit.picking_ids), 1)
        self.assertEqual(deposit.weight, self.delivery_order.shipping_weight)
        deposit.validate_deposit()
        self.assertEqual(deposit.state, "done")
