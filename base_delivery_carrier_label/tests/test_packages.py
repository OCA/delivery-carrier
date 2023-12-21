# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo_test_helper import FakeModelLoader

from .carrier_label_case import CarrierLabelCase


class TestCarrierPackages(CarrierLabelCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models.carrier_test import DeliveryCarrierTest
        from .models.stock_picking import StockPicking

        cls.loader.update_registry(
            (
                DeliveryCarrierTest,
                StockPicking,
            )
        )
        product = cls.env["product.product"].create(
            {
                "name": "Test Delivery Product",
                "type": "service",
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier Packages",
                "product_id": product.id,
                "delivery_type": "base_delivery_carrier_label",
            }
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.loader.restore_registry()
        super().tearDownClass()

    def _get_carrier(self):
        return self.carrier

    def test_labels_with_packages(self):
        """
        Test an example of label assignation to a picking's package
        """
        self.picking.carrier_id.automatic_package_creation_at_delivery = True
        self.picking.send_to_shipper()

        self.assertTrue(self.picking.has_packages)

        lines = self.picking.move_line_ids.filtered("package_level_id")

        self.assertEqual("123231-1", lines.package_level_id.package_id.parcel_tracking)

    def test_labels_without_packages(self):
        """
        Test an example of label assignation to a picking without package
        """
        self.picking.carrier_id.automatic_package_creation_at_delivery = False
        self.picking.send_to_shipper()
        self.assertFalse(self.picking.has_packages)
        self.assertEqual("123231", self.picking.carrier_tracking_ref)
