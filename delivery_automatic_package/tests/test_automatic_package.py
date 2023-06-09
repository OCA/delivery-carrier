# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, SavepointCase


class TestAutomaticPackage(SavepointCase):
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
        cls.product_packaging = cls.env["product.packaging"].create(
            {
                "name": "Box",
                "qty": "2",
                "product_id": cls.product.id,
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
        cls.env["stock.quant"]._update_available_quantity(
            cls.product,
            cls.stock,
            10,
        )
        cls.env.company.automatic_package_creation_at_delivery_default = True
        with Form(cls.env["delivery.carrier"]) as carrier_form:
            carrier_form.name = "Carrier Automatic Package"
            carrier_form.product_id = cls.product_delivery
        cls.carrier = carrier_form.save()
        cls.picking = cls._create_picking()
        cls.picking.move_lines.update({"quantity_done": 4.0})

    @classmethod
    def _create_picking(cls):
        vals = {
            "carrier_id": cls.carrier.id,
            "location_id": cls.stock.id,
            "location_dest_id": cls.customers.id,
            "picking_type_id": cls.env.ref("stock.picking_type_out").id,
            "move_lines": [
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

    def test_automatic_carrier_single(self):
        """
        Check that the automatic package creation is set on new carrier
        Create a picking, fill in quantities and validate it
        The move line should contain a package
        """
        self.assertTrue(self.carrier.automatic_package_creation_at_delivery)
        self.assertTrue(self.carrier.automatic_package_creation_mode, "single")
        self.picking._action_done()
        self.assertTrue(self.picking.move_line_ids.result_package_id)
        self.assertTrue(len(self.picking.move_line_ids.result_package_id), 1)

    def test_automatic_carrier_packaging(self):
        """
        Check that the automatic package creation is set on new carrier
        Create a picking, fill in quantities and validate it
        The move line should contain a package per product packaging
        """
        self.assertTrue(self.carrier.automatic_package_creation_at_delivery)
        self.carrier.automatic_package_creation_mode = "packaging"
        self.picking._action_done()
        self.assertTrue(self.picking.move_line_ids.result_package_id)
        self.assertTrue(len(self.picking.move_line_ids.result_package_id), 2)

    def test_automatic_context_single(self):
        """
        Check that the automatic package creation is set on new carrier
        Create a picking, fill in quantities and validate it with good
        context key
        The move line should contain a package
        """
        self.carrier.automatic_package_creation_at_delivery = False
        self.assertTrue(self.carrier.automatic_package_creation_mode, "single")
        self.picking.with_context(set_default_package=True)._action_done()
        self.assertTrue(self.picking.move_line_ids.result_package_id)
        self.assertTrue(len(self.picking.move_line_ids.result_package_id), 1)

    def test_no_automatic(self):
        """
        Disable the automatic package creation on carrier
        Create a picking, fill in quantities and validate it
        The move line should not contain a package
        """
        self.carrier.automatic_package_creation_at_delivery = False
        self.picking._action_done()
        self.assertFalse(self.picking.move_line_ids.result_package_id)
