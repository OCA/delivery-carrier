# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDeliveryDPDPortugal(TransactionCase):
    """Test DPD Portugal delivery carrier functionality."""

    def setUp(self):
        """Set up test data."""
        super().setUp()

        # Create test partners
        self.customer = self.env["res.partner"].create(
            {
                "name": "Test Customer",
                "street": "Test Street 123",
                "city": "Lisbon",
                "zip": "1000-001",
                "country_id": self.env.ref("base.pt").id,
                "email": "customer@test.com",
                "phone": "+351123456789",
            }
        )

        self.warehouse = self.env.ref("stock.warehouse0")
        self.warehouse.partner_id.write(
            {
                "street": "Warehouse Street 1",
                "city": "Porto",
                "zip": "4000-001",
                "country_id": self.env.ref("base.pt").id,
                "phone": "+351987654321",
            }
        )

        # Create DPD Portugal carrier
        self.dpd_carrier = self.env["delivery.carrier"].create(
            {
                "name": "DPD Portugal Test",
                "delivery_type": "dpd_pt",
                "dpd_portugal_service_type": "standard",
                "dpd_portugal_label_format": "PDF",
                "dpd_portugal_cod_enabled": True,
                "dpd_portugal_insurance_enabled": True,
                "dpd_portugal_insurance_amount": 100.0,
                "product_id": self.env.ref("delivery.product_product_delivery").id,
            }
        )

    def test_carrier_creation(self):
        """Test DPD Portugal carrier creation."""
        self.assertEqual(self.dpd_carrier.delivery_type, "dpd_pt")
        self.assertEqual(self.dpd_carrier.dpd_portugal_service_type, "standard")
        self.assertFalse(self.dpd_carrier.prod_environment)
        self.assertTrue(self.dpd_carrier.dpd_portugal_cod_enabled)

    def test_can_generate_return(self):
        """Test return shipment capability."""
        self.assertTrue(self.dpd_carrier.can_generate_return)

    def test_get_tracking_link(self):
        """Test tracking link generation."""
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.customer.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "carrier_id": self.dpd_carrier.id,
                "carrier_tracking_ref": "DPD123456789",
            }
        )

        tracking_link = self.dpd_carrier.dpd_pt_get_tracking_link(picking)
        self.assertIn("DPD123456789", tracking_link)
        self.assertIn("dpd.pt", tracking_link)

    def test_address_validation(self):
        """Test address validation."""
        # Valid address
        self.dpd_carrier._validate_dpd_pt_address(self.customer, "recipient")

        # Invalid address (missing required fields)
        invalid_partner = self.env["res.partner"].create({"name": "Invalid Partner"})
        with self.assertRaises(ValidationError):
            self.dpd_carrier._validate_dpd_pt_address(invalid_partner, "recipient")

    def test_api_url_selection(self):
        """Test API URL selection based on environment."""
        # Test environment
        test_url = self.dpd_carrier._dpd_pt_get_api_url()
        self.assertIn("qabusiness", test_url)

        # Production environment
        self.dpd_carrier.prod_environment = True
        prod_url = self.dpd_carrier._dpd_pt_get_api_url()
        self.assertIn("business.dpd.pt", prod_url)
        self.assertNotIn("qabusiness", prod_url)
