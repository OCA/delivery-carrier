# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestGetWeight(TransactionCase):
    """Test get_weight functions."""

    # some helpers
    def _create_order(self, customer):
        return self.env["sale.order"].create({"partner_id": customer.id})

    def _create_order_line(self, order, products):
        for product in products:
            self.env["sale.order.line"].create(
                {"product_id": product.id, "order_id": order.id}
            )

    def _create_ul(self):
        vals = [
            {"name": "Cardboard box", "type": "box", "weight": 0.200},
            {"name": "Wood box", "type": "box", "weight": 1.30},
        ]

        return [self.env["product.ul"].create(val) for val in vals]

    def _create_operation(self, picking, values):
        vals = {
            "picking_id": picking.id,
            "location_id": picking.location_id.id,
            "location_dest_id": picking.location_dest_id.id,
        }
        vals.update(values)
        return self.env["stock.move.line"].create(vals)

    def _create_product(self, vals):
        return self.env["product.product"].create(vals)

    def _get_products(self, weights):
        """Create fresh products with specific weights.

        Params:
            weights: list of weights, one product per weight
        """
        products = self.env["product.product"]
        for idx, w in enumerate(weights):
            products |= self.env["product.product"].create(
                {
                    "name": f"Test Weight Product {idx}",
                    "type": "consu",
                    "weight": w,
                }
            )
        return products

    def _generate_picking(self, products):
        """Create a picking with move lines for given products."""
        customer = self.env["res.partner"].create({"name": "Test Customer"})
        picking_type = self.env.ref("stock.picking_type_out")
        picking = self.env["stock.picking"].create(
            {
                "partner_id": customer.id,
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": picking_type.default_location_dest_id.id,
            }
        )
        return picking

    def test_get_weight(self):
        """Test quant.package.weight computed field and
        pack.operation.get_weight."""
        # prepare some data
        weights = [2, 30, 1, 24, 39]
        products = self._get_products(weights)
        picking = self._generate_picking(products)
        package = self.env["stock.quant.package"].create({})
        operations = self.env["stock.move.line"]
        for product in products:
            operations |= self._create_operation(
                picking,
                {
                    "quantity": 1,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "result_package_id": package.id,
                },
            )
        # end of prepare data

        # test operation.get_weight()
        for operation in operations:
            self.assertEqual(
                operation.get_weight(),
                operation.product_id.weight * operation.quantity,
            )

        # test package.weight
        self.assertEqual(package.weight, sum(product.weight for product in products))

    def test_total_weight(self):
        """Test quant.package.weight computed field when a total
        weight is defined"""
        # prepare some data
        weights = [2, 30, 1, 24, 39]
        products = self._get_products(weights)
        picking = self._generate_picking(products)
        package = self.env["stock.quant.package"].create({})
        operations = self.env["stock.move.line"]
        for product in products:
            operations |= self._create_operation(
                picking,
                {
                    "quantity": 1,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "result_package_id": package.id,
                },
            )
        package.shipping_weight = 1542.0
        # end of prepare data

        # test operation.get_weight()
        for operation in operations:
            self.assertEqual(
                operation.get_weight(),
                operation.product_id.weight * operation.quantity,
            )

        # test package.weight
        self.assertEqual(package.weight, package.shipping_weight)

    def test_get_weight_with_qty(self):
        """Ensure qty are taken in account."""
        # prepare some data
        weights = [2, 30, 1, 24, 39]
        products = self._get_products(weights)
        picking = self._generate_picking(products)
        package = self.env["stock.quant.package"].create({})
        operations = self.env["stock.move.line"]
        for idx, product in enumerate(products):
            operations |= self._create_operation(
                picking,
                {
                    "quantity": idx,  # nice one
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "result_package_id": package.id,
                },
            )
        # end of prepare data

        # test operation.get_weight()
        for operation in operations:
            self.assertEqual(
                operation.get_weight(),
                operation.product_id.weight * operation.quantity,
            )

        # test package._weight
        self.assertEqual(
            package.weight, sum(operation.get_weight() for operation in operations)
        )

    def test_get_weight_with_uom(self):
        """Check with differents uom."""
        # prepare some data
        weights = [0.3, 14.01, 0.59]
        package = self.env["stock.quant.package"].create({})
        tonne_id = self.env.ref("uom.product_uom_ton")
        kg_id = self.env.ref("uom.product_uom_kgm")
        gr_id = self.env.ref("uom.product_uom_gram")
        products = []
        products.append(
            self._create_product(
                {
                    "name": "Expected Odoo dev documentation",
                    "uom_id": tonne_id.id,
                    "uom_po_id": tonne_id.id,
                    "weight": weights[0],
                }
            )
        )
        products.append(
            self._create_product(
                {
                    "name": "OCA documentation",
                    "uom_id": kg_id.id,
                    "uom_po_id": kg_id.id,
                    "weight": weights[1],
                }
            )
        )
        products.append(
            self._create_product(
                {
                    "name": "Actual Odoo dev documentation",
                    "uom_id": gr_id.id,
                    "uom_po_id": gr_id.id,
                    "weight": weights[2],
                }
            )
        )
        products_weight = (
            weights[0] * 1000 + weights[1] * 1 + weights[2] * 0.01  # tonne  # kg  # g
        )
        picking = self._generate_picking(products)
        operations = self.env["stock.move.line"]
        for product in products:
            operations |= self._create_operation(
                picking,
                {
                    "quantity": 1,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "result_package_id": package.id,
                },
            )
        # end of prepare data

        # because uom conversion is not implemented
        self.assertEqual(package.weight, False)

        # if one day, uom conversion is implemented:
        # self.assertEqual(package.get_weight(), products_weight)
        self.assertEqual(products_weight, products_weight)  # flak8 warning
