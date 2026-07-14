# Copyright 2024 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo_test_helper import FakeModelLoader

from odoo.fields import Command


class CommonChooseDeliveryPackage:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "is_storable": True,
            }
        )

        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": cls.product.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "inventory_quantity": 10.0,
            }
        )._apply_inventory()

    def setUp(self):
        super().setUp()
        self.loader = FakeModelLoader(self.env, self.__module__)
        self.loader.backup_registry()

        from .models.test import DeliveryCarrier, StockPackageType

        self.loader.update_registry((DeliveryCarrier, StockPackageType))

        self.delivery_obj = self.env["delivery.carrier"]
        self.package_type_obj = self.env["stock.package.type"]
        self.package_type = self.package_type_obj.create(
            {
                "name": "Type Test",
                "package_carrier_type": "test",
            }
        )
        self.product_delivery = self.env["product.product"].create(
            {
                "name": "Delivery Product",
                "type": "service",
            }
        )
        self.delivery = self.delivery_obj.create(
            {
                "name": "Test",
                "delivery_type": "test",
                "product_id": self.product_delivery.id,
            }
        )

    def _create_sale(self):
        self.sale = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "carrier_id": self.delivery.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 5.0,
                        }
                    )
                ],
            }
        )
        return self.sale

    def tearDown(self):
        self.loader.restore_registry()
        super().tearDown()
