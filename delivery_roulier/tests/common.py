# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo_test_helper import FakeModelLoader
from roulier import roulier

from odoo.addons.base.tests.common import BaseCommon


class DeliveryRoulierCommonCase(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.real_get_carriers_action_available = roulier.get_carriers_action_available

    def setUp(self):
        super().setUp()

        self.loader = FakeModelLoader(self.env, self.__module__)
        self.loader.backup_registry()

        # The fake class is imported here !! After the backup_registry
        from .models import FakeDeliveryCarrier, Package

        self.loader.update_registry((FakeDeliveryCarrier, Package))
        delivery_product = self.env["product.product"].create(
            {"name": "test shipping product", "type": "service"}
        )
        self.account = self.env["carrier.account"].create(
            {
                "name": "Test Carrier Account",
                "delivery_type": "test",
                "account": "test",
                "password": "test",
            }
        )
        self.test_carrier = self.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "test",
                "product_id": delivery_product.id,
                "carrier_account_id": self.account.id,
            }
        )
        partner = self.env["res.partner"].create(
            {
                "name": "Carrier label test customer",
                "country_id": self.env.ref("base.fr").id,
                "street": "test street",
                "street2": "test street2",
                "city": "test city",
                "phone": "0000000000",
                "email": "test@test.com",
                "zip": "00000",
            }
        )
        product = self.env.ref("delivery_roulier.product_small")
        self.order = self.env["sale.order"].create(
            {
                "carrier_id": self.test_carrier.id,
                "partner_id": partner.id,
                "order_line": [
                    (0, 0, {"product_id": product.id, "product_uom_qty": 1})
                ],
            }
        )
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": product.id,
                "location_id": self.order.warehouse_id.lot_stock_id.id,
                "inventory_quantity": 1,
            }
        ).action_apply_inventory()
        self.order.action_confirm()
        self.picking = self.order.picking_ids

    def tearDown(self):
        self.loader.restore_registry()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        roulier.get_carriers_action_available = cls.real_get_carriers_action_available
        super().tearDownClass()
