# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import pytest

from odoo.tests.common import TransactionCase


class ChronopostLabelCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        # need it to be defined before super to avoid failure in _hide_sensitive_data
        cls.account = False
        super().setUpClass()
        # change account and password with valid credentials to regenerate the cassette
        cls.account = cls.env["carrier.account"].create(
            {
                "name": "Chronopost Test Account",
                "delivery_type": "chronopost_fr",
                "account": "dummy",
                "password": "dummy",
                "chronopost_fr_file_format": "Z2D",
            }
        )
        cls.picking = cls._create_order_picking()
        # french carrier sender need to be from France
        cls.picking.company_id.partner_id.write(
            {"country_id": cls.env.ref("base.fr").id}
        )

    @classmethod
    def _create_order_picking(cls):
        """Create a sale order and deliver the picking"""
        cls.order = cls.env["sale.order"].create(cls._sale_order_data())
        for product in cls.order.mapped("order_line.product_id"):
            cls.env["stock.quant"].with_context(inventory_mode=True).create(
                {
                    "product_id": product.id,
                    "location_id": cls.order.warehouse_id.lot_stock_id.id,
                    "inventory_quantity": sum(
                        cls.order.mapped("order_line.product_uom_qty")
                    ),
                }
            )._apply_inventory()
        cls.order.action_confirm()
        cls.picking = cls.order.picking_ids
        cls.picking.write(cls._picking_data())
        return cls.picking

    @classmethod
    def _get_carrier(cls):
        return cls.env.ref("delivery_roulier_chronopost_fr.chrono_13")

    @classmethod
    def _sale_order_data(cls):
        """Return a values dict to create a sale order"""
        return {
            "partner_id": cls.env["res.partner"].create(cls._partner_data()).id,
            "order_line": [(0, 0, data) for data in cls._order_line_data()],
            "carrier_id": cls._get_carrier().id,
        }

    @classmethod
    def _partner_data(cls):
        """Return a values dict to create a partner"""
        return {
            "name": "Carrier label test customer",
            "street": "27 Rue Henri Rolland",
            "zip": "69100",
            "city": "VILLEURBANNE",
            "country_id": cls.env.ref("base.fr").id,
        }

    @classmethod
    def _order_line_data(cls):
        """Return a list of value dicts to create order lines"""
        return [
            {
                "product_id": cls.env["product.product"].create(cls._product_data()).id,
                "product_uom_qty": 1,
            }
        ]

    @classmethod
    def _product_data(cls):
        """Return a values dict to create a product"""
        return {"name": "Carrier test product", "type": "product", "weight": 1.2}

    @classmethod
    def _picking_data(cls):
        """Return a values dict to be written to the picking in order to set
        carrier options"""
        return {}

    @classmethod
    def _hide_sensitive_data(cls, request):
        password = cls.account and cls.account.password
        account = cls.account and cls.account.account
        body = request.body
        body = body.replace(password.encode(), b"password")
        body = body.replace(account.encode(), b"00000000")
        request.body = body
        return request

    @classmethod
    @pytest.fixture(scope="module")
    def vcr_config(cls):
        return {
            "filter_headers": ["authorization"],
            "ignore_localhost": True,
            "record_mode": "once",
            "match_on": ["method", "path"],
            "decode_compressed_response": True,
            "before_record_request": cls._hide_sensitive_data,
        }

    @pytest.mark.default_cassette("test_roulier_chronopost_fr.yaml")
    @pytest.mark.block_network
    @pytest.mark.vcr
    def test_roulier_chronopost_fr(self):
        self.picking.with_context(dummy_account_id=self.account.id).button_validate()
