# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDeliveryNacex(TransactionCase):
    """Test NACEX delivery carrier functionality."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.company = self.env.ref("base.main_company")

        # Create test partners
        self.customer = self._create_partner("Test Customer")
        self.shipper = self._create_partner("Test Shipper")

        # Create test product
        self.product = self._create_product("Test Product")

        # Create NACEX carrier
        self.nacex_carrier = self._create_nacex_carrier()

        # Create carrier account
        self.carrier_account = self._create_carrier_account()

    # ==================== HELPER METHODS ====================

    def _create_partner(self, name):
        """Create a test partner with complete address."""
        return self.env["res.partner"].create(
            {
                "name": name,
                "street": "Test Street 123",
                "city": "Test City",
                "zip": "28001",
                "country_id": self.env.ref("base.es").id,
                "phone": "912345678",
                "email": f"{name.lower().replace(' ', '_')}@test.com",
                "is_company": True,
            }
        )

    def _create_product(self, name):
        """Create a test product."""
        return self.env["product.product"].create(
            {
                "name": name,
                "type": "consu",
                "default_code": f"PROD{name[-3:]}" if len(name) > 3 else "PROD",
                "weight": 1.5,
                "list_price": 100.0,
            }
        )

    def _create_nacex_carrier(self):
        """Create a NACEX delivery carrier with all required fields."""
        # Get or create delivery product
        delivery_product = self.env["product.product"].search(
            [("default_code", "=", "DELIVERY")], limit=1
        ) or self.env["product.product"].create({"name": "Delivery", "type": "service"})
        return self.env["delivery.carrier"].create(
            {
                "name": "NACEX Test Carrier",
                "delivery_type": "nacex",
                "product_id": delivery_product.id,
                "nacex_agency_code": "1234",
                "nacex_customer_code": "CLIENT123",
                "nacex_service_code": "01",
                "nacex_carriage_code": "O",
                "nacex_packaging_code": "1",
                "nacex_with_return": False,
            }
        )

    def _create_carrier_account(self):
        """Create a carrier account for NACEX."""
        return self.env["carrier.account"].create(
            {
                "name": "NACEX Account",
                "delivery_type": "nacex",
                "account": "test_user",
                "password": "test_pass",
                "company_id": self.company.id,
            }
        )

    def _create_sale_order(self, carrier=None):
        """Create a test sale order."""
        if carrier is None:
            carrier = self.nacex_carrier

        return self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                            "price_unit": 100.0,
                        },
                    )
                ],
                "carrier_id": carrier.id,
            }
        )

    def _create_stock_picking(self, carrier=None):
        """Create a test stock picking."""
        if carrier is None:
            carrier = self.nacex_carrier

        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.customer.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "carrier_id": carrier.id,
                "origin": "TEST001",
            }
        )

        # Add moves
        self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "product_uom": self.product.uom_id.id,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
                "picking_id": picking.id,
            }
        )

        return picking

    def _assign_carrier_account_to_picking(self, picking, account=None):
        """Assign carrier account to picking."""
        if account is None:
            account = self.carrier_account

        # Link the carrier account to the carrier
        self.nacex_carrier.carrier_account_id = account

    # ==================== TEST METHODS ====================

    def test_01_nacex_carrier_creation(self):
        """Test: NACEX carrier can be created with required fields."""
        # Step 1: Verify carrier exists from setUp
        self.assertIsNotNone(self.nacex_carrier)
        self.assertEqual(self.nacex_carrier.delivery_type, "nacex")
        self.assertEqual(self.nacex_carrier.nacex_agency_code, "1234")
        self.assertEqual(self.nacex_carrier.nacex_customer_code, "CLIENT123")

    def test_02_nacex_tracking_link_generation(self):
        """Test: NACEX tracking link generation."""
        # Step 1: Create picking with tracking
        picking = self._create_stock_picking()
        picking.carrier_tracking_ref = "TEST123456"

        # Step 2: Generate tracking link
        tracking_link = self.nacex_carrier.nacex_get_tracking_link(picking)

        # Step 3: Verify tracking link format
        self.assertIsNotNone(tracking_link)
        self.assertIn("nacex.com", tracking_link)
        self.assertIn("TEST123456", tracking_link)

    def test_03_nacex_agency_code_resolution(self):
        """Test: NACEX agency code resolution from warehouse."""
        # Step 1: Create picking
        picking = self._create_stock_picking()

        # Step 2: Get agency code
        agency_code = self.nacex_carrier._nacex_get_agency_code(picking)

        # Step 3: Verify agency code
        self.assertIsNotNone(agency_code)
        self.assertEqual(agency_code, "1234")

    def test_04_nacex_with_return_field_inheritance(self):
        """Test: NACEX with_return field inherited in stock.picking."""
        # Step 1: Create picking with NACEX carrier
        picking = self._create_stock_picking()

        # Step 2: Verify nacex_with_return field exists
        self.assertIn("nacex_with_return", picking._fields)

        # Step 3: Test field value defaults to carrier setting
        self.assertEqual(
            picking.nacex_with_return,
            self.nacex_carrier.nacex_with_return,
        )

    def test_05_carrier_account_integration(self):
        """Test: Carrier account integration with NACEX."""
        # Step 1: Create picking
        picking = self._create_stock_picking()

        # Step 2: Assign carrier account
        self._assign_carrier_account_to_picking(picking)

        # Step 3: Verify account can be retrieved
        account = picking._get_carrier_account()
        self.assertIsNotNone(account)
        self.assertEqual(account.account, "test_user")
        self.assertEqual(account.password, "test_pass")
        self.assertEqual(account.delivery_type, "nacex")
