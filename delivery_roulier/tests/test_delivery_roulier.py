# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import MagicMock, patch

from roulier import roulier

from odoo.exceptions import UserError

from .common import DeliveryRoulierCommonCase

roulier_ret = {
    "parcels": [
        {
            "reference": "",
            "tracking": {"url": "", "number": "test_tracking"},
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


class DeliveryRoulierCase(DeliveryRoulierCommonCase):
    def test_roulier_no_pack(self):
        # having a pack is mandatory for roulier
        # it should fail if no pack provided.
        # in <16 packs were silently created
        roulier.get_carriers_action_available = MagicMock(
            return_value={"test": ["get_label"]}
        )
        with patch("roulier.roulier.get") as mock_roulier:
            mock_roulier.return_value = roulier_ret
            self.assertRaises(UserError, self.picking.send_to_shipper)

    def test_roulier(self):
        roulier.get_carriers_action_available = MagicMock(
            return_value={"test": ["get_label"]}
        )
        with patch("roulier.roulier.get") as mock_roulier:
            mock_roulier.return_value = roulier_ret

            # create pack
            move_lines = self.picking.move_line_ids.filtered(
                lambda s: not s.result_package_id
            )
            if move_lines:
                self.picking._put_in_pack(move_lines)

            self.picking.send_to_shipper()

            roulier_args = mock_roulier.mock_calls[0][1]
            self.assertEqual("get_label", roulier_args[1])
            roulier_payload = roulier_args[2]
            self.assertEqual(len(roulier_payload["parcels"]), 1)
            self.assertEqual(roulier_payload["parcels"][0].get("weight"), 1.3)
            self.assertEqual(
                roulier_payload["to_address"].get("street1"), "test street"
            )
            self.assertEqual(roulier_payload["to_address"].get("country"), "FR")
            self.assertEqual(roulier_payload["auth"].get("isTest"), True)
            self.assertEqual(roulier_payload["auth"].get("login"), "test")

            # Test tracking on pack / existing shipping label and tracking url
            package = self.picking.move_line_ids.result_package_id
            self.assertEqual(len(package), 1)
            self.assertEqual(package.parcel_tracking, "test_tracking")
            shipping_label = self.env["shipping.label"].search(
                [("res_id", "=", self.picking.id)]
            )
            self.assertEqual(len(shipping_label), 1)
            package_tracking_action = self.picking.open_website_url()
            self.assertEqual(package_tracking_action["type"], "ir.actions.act_url")
            self.assertEqual(
                package_tracking_action["url"], "http://www.test.com/test_tracking"
            )
