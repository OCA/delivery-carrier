# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import MagicMock, patch

from odoo_test_helper import FakeModelLoader
from roulier import roulier

from odoo.tests.common import TransactionCase

roulier_ret = {
    "parcels": [
        {
            "reference": "",
            "tracking": {"url": "", "number": "Test tracking"},
            "label": {
                "name": "label_test",
                "data": b"dGVzdCBsYWJlbA==",
                "type": "zpl2",
            },
            "id": 1,
        }
    ],
    "annexes": [{"name": "annexe name", "type": "txt", "data": b"dGVzdCBhbm5leGU="}],
}


class DeliveryRoulierCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        # The fake class is imported here !! After the backup_registry
        from .models import FakeDeliveryCarrier

        cls.loader.update_registry((FakeDeliveryCarrier,))
        cls.real_get_carriers_action_available = roulier.get_carriers_action_available
        delivery_product = cls.env["product.product"].create(
            {"name": "test shipping product", "type": "service"}
        )
        cls.account = cls.env["carrier.account"].create(
            {
                "name": "Test Carrier Account",
                "delivery_type": "test",
                "account": "test",
                "password": "test",
            }
        )
        cls.test_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "test",
                "product_id": delivery_product.id,
                "carrier_account_id": cls.account.id,
            }
        )
        partner = cls.env["res.partner"].create(
            {
                "name": "Carrier label test customer",
                "country_id": cls.env.ref("base.fr").id,
                "street": "test street",
                "street2": "test street2",
                "city": "test city",
                "phone": "0000000000",
                "email": "test@test.com",
                "zip": "00000",
            }
        )
        product = cls.env["product.product"].create(
            {"name": "Carrier test product", "type": "product", "weight": 1.2}
        )
        cls.order = cls.env["sale.order"].create(
            {
                "carrier_id": cls.test_carrier.id,
                "partner_id": partner.id,
                "order_line": [
                    (0, 0, {"product_id": product.id, "product_uom_qty": 1})
                ],
            }
        )
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": product.id,
                "location_id": cls.order.warehouse_id.lot_stock_id.id,
                "inventory_quantity": 1,
            }
        ).action_apply_inventory()
        cls.order.action_confirm()
        cls.picking = cls.order.picking_ids

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        roulier.get_carriers_action_available = cls.real_get_carriers_action_available
        super().tearDownClass()

    def test_roulier(self):
        roulier.get_carriers_action_available = MagicMock(
            return_value={"test": ["get_label"]}
        )
        with patch("roulier.roulier.get") as mock_roulier:
            mock_roulier.return_value = roulier_ret
            self.picking.send_to_shipper()
            roulier_args = mock_roulier.mock_calls[0][1]
            self.assertEqual("get_label", roulier_args[1])
            roulier_payload = roulier_args[2]
            self.assertEqual(len(roulier_payload["parcels"]), 1)
            self.assertEqual(roulier_payload["parcels"][0].get("weight"), 1.2)
            self.assertEqual(
                roulier_payload["to_address"].get("street1"), "test street"
            )
            self.assertEqual(roulier_payload["to_address"].get("country"), "FR")
            self.assertEqual(roulier_payload["auth"].get("isTest"), True)
            self.assertEqual(roulier_payload["auth"].get("login"), "test")
