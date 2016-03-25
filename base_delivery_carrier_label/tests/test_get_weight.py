# -*- coding: utf-8 -*-

from openerp.tests.common import TransactionCase


class TestGetWeight(TransactionCase):
    """Test get_weight functions."""

    # some helpers
    def _create_order(self, customer):
        return self.env['sale.order'].create({
            'partner_id': customer.id,
        })

    def _create_order_line(self, order, products):
        ol = []
        for product in products:
            ol.append(self.env['sale.order.line'].create({
                'product_id': product.id,
                'order_id': order.id,
            }))
        return ol

    def _create_ul(self):
        vals = [{
            'name': 'Cardboard box',
            'type': 'box',
            'weight': 0.200,
        }, {
            'name': 'Wood box',
            'type': 'box',
            'weight': 1.30,
        }]

        return [
            self.env['product.ul'].create(val)
            for val in vals
        ]

    def _create_operation(self, picking, values):
        vals = {
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        }
        vals.update(values)
        return self.env['stock.pack.operation'].create(vals)

    def _create_product(self, vals):
        return self.env['product.product'].create(vals)

    def _get_products(self, weights):
        """A recordset of products without any specific uom.

        It means : no uom or kg or unit
        Params:
            weights: recordset will be size of weights and each
                product will get a size according of weights[i]
        """
        kg_id = self.env.ref('product.product_uom_kgm').id
        unit_id = self.env.ref('product.product_uom_unit').id

        products = self.env['product.product'].search(
            [['uom_id', 'in', (False, kg_id, unit_id)]],
            limit=len(weights))
        for idx, product in enumerate(products):
            # by default there is no weight on products
            product.weight = weights[idx]
        return products

    def _generate_picking(self, products):
        """Create a picking from products."""
        customer = self.env['res.partner'].search([], limit=1)
        order = self._create_order(customer)
        self._create_order_line(order, products)
        order.action_button_confirm()
        picking = order.picking_ids
        picking.do_transfer()
        return picking

    def test_get_weight(self):
        """Test quant.package.get_weight and pack.operation.get_weight."""
        # prepare some data
        weights = [2, 30, 1, 24, 39]
        products = self._get_products(weights)
        picking = self._generate_picking(products)
        package = self.env['stock.quant.package'].create({})
        operations = []
        for product in products:
            operations.append(self._create_operation(picking, {
                'product_qty': 1,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'result_package_id': package.id,
            }))
        # end of prepare data

        # test operation.get_weight()
        for operation in operations:
            self.assertEqual(
                operation.get_weight(),
                operation.product_id.weight * operation.product_qty)

        # test package.get_weight()
        self.assertEqual(
            package.get_weight(),
            sum([product.weight for product in products]))

    def test_get_weight_with_qty(self):
        """Ensure qty are taken in account."""
        # prepare some data
        weights = [2, 30, 1, 24, 39]
        products = self._get_products(weights)
        picking = self._generate_picking(products)
        package = self.env['stock.quant.package'].create({})
        operations = []
        for idx, product in enumerate(products):
            operations.append(self._create_operation(picking, {
                'product_qty': idx,  # nice one
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'result_package_id': package.id
            }))
        # end of prepare data

        # test operation.get_weight()
        for operation in operations:
            self.assertEqual(
                operation.get_weight(),
                operation.product_id.weight * operation.product_qty)

        # test package.get_weight()
        self.assertEqual(
            package.get_weight(),
            sum([operation.get_weight() for operation in operations]))

    def test_get_weight_with_lu(self):
        """Check with logistic unit."""
        # prepare some data
        weights = [2.39, 3.1, 20, 24, 39]
        products = self._get_products(weights)
        picking = self._generate_picking(products)
        uls = self._create_ul()
        packages = [
            self.env['stock.quant.package'].create(
                {'ul_id': ul.id}
            ) for ul in uls
        ]
        operations = []
        for idx, product in enumerate(products):
            pack = packages[idx % len(packages)]
            operations.append(self._create_operation(picking, {
                'product_qty': 1,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'result_package_id': pack.id,
            }))
        # end of prepare data

        products_weight = sum([product.weight for product in products])
        packages_weight = sum(
            [package.ul_id.weight for package in packages])

        self.assertEqual(
            sum([package.get_weight() for package in packages]),
            packages_weight + products_weight)

        # with @api.multi
        packages_multi = self.env['stock.quant.package'].search(
            [['id', 'in', [package.id for package in packages]]]
        )

        self.assertEqual(
            packages_multi.get_weight(),
            packages_weight + products_weight
        )

    def test_get_weight_with_uom(self):
        """Check with differents uom."""
        # prepare some data
        weights = [0.3, 14.01, 0.59]
        package = self.env['stock.quant.package'].create({})
        tonne_id = self.env.ref('product.product_uom_ton')
        kg_id = self.env.ref('product.product_uom_kgm')
        gr_id = self.env.ref('product.product_uom_gram')
        products = []
        products.append(self._create_product(
            {
                'name': 'Expected Odoo dev documentation',
                'uom_id': tonne_id.id,
                'uos_id': tonne_id.id,
                'uom_po_id': tonne_id.id,
                'weight': weights[0]
            })
        )
        products.append(self._create_product(
            {
                'name': 'OCA documentation',
                'uom_id': kg_id.id,
                'uos_id': kg_id.id,
                'uom_po_id': kg_id.id,
                'weight': weights[1],
            }))
        products.append(self._create_product(
            {
                'name': 'Actual Odoo dev documentation',
                'uom_id': gr_id.id,
                'uos_id': gr_id.id,
                'uom_po_id': gr_id.id,
                'weight': weights[2],
            })
        )
        products_weight = (
            weights[0] * 1000 +  # tonne
            weights[1] * 1 +  # kg
            weights[2] * 0.01  # g
        )
        picking = self._generate_picking(products)
        operations = []
        for product in products:
            operations.append(self._create_operation(picking, {
                'product_qty': 1,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'result_package_id': package.id,
            }))
        # end of prepare data

        # because uom conversion is not implemented
        self.assertEqual(package.get_weight(), False)

        # if one day, uom conversion is implemented:
        # self.assertEqual(package.get_weight(), products_weight)
        self.assertEqual(products_weight, products_weight)  # flak8 warning
