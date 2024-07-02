# Copyright 2024 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo_test_helper import FakeModelLoader

from odoo.fields import Command


class CommonChooseDeliveryPackage:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        from .models.test import DeliveryCarrier, StockPackageType

        cls.loader.update_registry((DeliveryCarrier, StockPackageType))

        cls.delivery_obj = cls.env["delivery.carrier"]
        cls.package_type_obj = cls.env["stock.package.type"]
        cls.package_type = cls.package_type_obj.create(
            {
                "name": "Type Test",
                "package_carrier_type": "test",
            }
        )
        cls.product_delivery = cls.env["product.product"].create(
            {
                "name": "Delivery Product",
                "type": "service",
            }
        )
        cls.delivery = cls.delivery_obj.create(
            {
                "name": "Test",
                "delivery_type": "test",
                "product_id": cls.product_delivery.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )

        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": cls.product.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "inventory_quantity": 10.0,
            }
        )._apply_inventory()

    @classmethod
    def _create_sale(cls):
        cls.sale = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "carrier_id": cls.delivery.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 5.0,
                        }
                    )
                ],
            }
        )
        return cls.sale

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()
