# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from roulier import roulier

from odoo.tests import RecordCapturer

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case

ROULIER_RESPONSE = {
    "parcels": [
        {
            "reference": "",
            "tracking": {
                "url": (
                    "https://www.chronopost.fr/tracking-no-cms/suivi-page"
                    "?listeNumerosLT=XP000000001FR"
                ),
                "number": "XP000000001FR",
            },
            "label": {
                "name": "chronopost_label",
                "data": b"dGVzdCBsYWJlbA==",
                "type": "zpl2",
            },
        }
    ],
    "annexes": [],
}


class TestChronopostLabel(carrier_label_case.CarrierLabelCase):
    """Test Chronopost label generation through Roulier."""

    transfer_in_setup = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls.env["carrier.account"].create(
            {
                "name": "Chronopost Test Account",
                "delivery_type": "chronopost_fr",
                "account": "dummy",
                "password": "dummy",
                "chronopost_fr_subaccount": "001",
                "chronopost_fr_file_format": "Z2D",
            }
        )
        cls.carrier = cls._get_carrier()
        cls.carrier.carrier_account_id = cls.account
        # Chronopost requires the sender address to be located in France.
        cls.picking.company_id.partner_id.write(
            {
                "street": "18 Rue de la République",
                "zip": "69002",
                "city": "Lyon",
                "country_id": cls.env.ref("base.fr").id,
            }
        )
        cls.picking.move_ids.quantity = cls.picking.move_ids.product_uom_qty

    @classmethod
    def _get_carrier(cls):
        """Return the Chronopost carrier under test."""
        return cls.env.ref("delivery_roulier_chronopost_fr.chrono_13")

    @classmethod
    def _partner_data(cls):
        """Return an explicit French recipient address."""
        values = super()._partner_data()
        values.update(
            {
                "street": "27 Rue Henri Rolland",
                "zip": "69100",
                "city": "Villeurbanne",
                "country_id": cls.env.ref("base.fr").id,
            }
        )
        return values

    @classmethod
    def _product_data(cls):
        """Return an explicit storable product with a shipping weight."""
        values = super()._product_data()
        values.update({"type": "product", "weight": 1.2})
        return values

    @patch.object(
        roulier,
        "get_carriers_action_available",
        return_value={"chronopost_fr": ["get_label"]},
    )
    @patch.object(roulier, "get", return_value=ROULIER_RESPONSE)
    def test_00_roulier_chronopost_fr_label(self, mocked_get, _mocked_actions):
        """Test validating a picking creates a label with a Chronopost payload."""
        label_domain = [
            ("res_id", "=", self.picking.id),
            ("res_model", "=", "stock.picking"),
        ]
        with RecordCapturer(self.env["shipping.label"], label_domain) as labels:
            self.picking.button_validate()

        mocked_get.assert_called_once()
        carrier_name, action, payload = mocked_get.call_args.args
        self.assertEqual(carrier_name, "chronopost_fr")
        self.assertEqual(action, "get_label")
        self.assertEqual(payload["auth"]["login"], "dummy")
        self.assertEqual(payload["auth"]["subAccount"], "001")
        self.assertEqual(payload["service"]["product"], "01")
        self.assertEqual(payload["service"]["labelFormat"], "Z2D")
        self.assertEqual(payload["service"]["service"], "0")
        self.assertEqual(payload["service"]["shippingId"], self.picking.name)
        self.assertEqual(payload["service"]["customerId"], self.picking.origin)
        self.assertIsInstance(payload["service"]["shippingHour"], int)
        self.assertEqual(payload["from_address"]["civility"], "E")
        self.assertEqual(payload["from_address"]["street1"], "18 Rue de la République")
        self.assertEqual(payload["from_address"]["preAlert"], 0)
        self.assertEqual(payload["to_address"]["street1"], "27 Rue Henri Rolland")
        self.assertEqual(payload["to_address"]["preAlert"], 0)
        self.assertEqual(payload["parcels"][0]["objectType"], "MAR")
        self.assertEqual(payload["parcels"][0]["weight"], 1.2)
        self.assertEqual(len(labels.records), 1)
        self.assertEqual(labels.records.name, "XP000000001FR.zpl2")
        self.assertEqual(labels.records.file_type, "zpl2")
        self.assertEqual(labels.records.datas, b"dGVzdCBsYWJlbA==")
        self.assertEqual(labels.records.package_id, self.picking.package_ids)
        self.assertEqual(self.picking.carrier_tracking_ref, "XP000000001FR")
        self.assertEqual(self.picking.package_ids.parcel_tracking, "XP000000001FR")
        self.assertEqual(
            self.picking.package_ids.parcel_tracking_uri,
            ROULIER_RESPONSE["parcels"][0]["tracking"]["url"],
        )
