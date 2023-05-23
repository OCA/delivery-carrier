# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class TestAutomaticPackage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Test",
                "type": "product",
            }
        )
        cls.product_delivery = cls.env["product.product"].create(
            {
                "name": "Delivery Test",
                "type": "service",
            }
        )
        cls.stock = cls.env.ref("stock.stock_location_stock")
        cls.customers = cls.env.ref("stock.stock_location_customers")
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "location_id": cls.stock.id,
                "product_id": cls.product.id,
                "quantity": 10.0,
            }
        )._apply_inventory()
        cls.env.company.automatic_package_creation_at_delivery_default = True
        with Form(cls.env["delivery.carrier"]) as carrier_form:
            carrier_form.name = "Carrier Automatic Package"
            carrier_form.product_id = cls.product_delivery
        cls.carrier = carrier_form.save()

    @classmethod
    def _create_picking(cls):
        vals = {
            "carrier_id": cls.carrier.id,
            "location_id": cls.stock.id,
            "location_dest_id": cls.customers.id,
            "picking_type_id": cls.env.ref("stock.picking_type_out").id,
            "move_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Product Test",
                        "location_id": cls.stock.id,
                        "location_dest_id": cls.customers.id,
                        "product_id": cls.product.id,
                        "product_uom_qty": 5.0,
                        "product_uom": cls.product.uom_id.id,
                    },
                )
            ],
        }
        return cls.env["stock.picking"].create(vals)

    def test_automatic_carrier(self):
        """
        Check that the automatic package creation is set on new carrier
        Create a picking, fill in quantities and validate it
        The move line should contain a package
        """
        self.assertTrue(self.carrier.automatic_package_creation_at_delivery)
        picking = self._create_picking()
        picking.move_ids.update({"quantity_done": 5.0})
        picking._action_done()
        self.assertTrue(picking.move_line_ids.result_package_id)

    def test_automatic_context(self):
        """
        Check that the automatic package creation is set on new carrier
        Create a picking, fill in quantities and validate it with good
        context key
        The move line should contain a package
        """
        self.carrier.automatic_package_creation_at_delivery = False
        picking = self._create_picking()
        picking.move_ids.update({"quantity_done": 5.0})
        picking.with_context(set_default_package=True)._action_done()
        self.assertTrue(picking.move_line_ids.result_package_id)

    def test_no_automatic(self):
        """
        Disable the automatic package creation on carrier
        Create a picking, fill in quantities and validate it
        The move line should not contain a package
        """
        self.carrier.automatic_package_creation_at_delivery = False
        picking = self._create_picking()
        picking.move_ids.update({"quantity_done": 5.0})
        picking._action_done()
        self.assertFalse(picking.move_line_ids.result_package_id)
