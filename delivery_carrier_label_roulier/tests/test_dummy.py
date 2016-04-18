# -*- coding: utf-8 -*-

from openerp.tests.common import TransactionCase

#TODO
#definir ce qu'on fait si on a pas mis de package.
#Rendre ça obligatoire ?

class TestDummy(TransactionCase):
    """Test dumy functions."""

    # some helpers
    def _create_order(self, customer, carrier=None):
        vals = {
            'partner_id': customer.id,
        }
        if carrier:
            vals['carrier_id'] = carrier
        return self.env['sale.order'].create(vals)

    def _create_order_line(self, order, products):
        ol = []
        for product in products:
            ol.append(self.env['sale.order.line'].create({
                'product_id': product.id,
                'order_id': order.id,
            }))
        return ol

    def _create_operation(self, picking, values):
        vals = {
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        }
        vals.update(values)
        return self.env['stock.pack.operation'].create(vals)

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

    def _generate_picking(self, products, is_dummy=True):
        """Create a picking from products."""
        dummy_product = self.env.ref(
            'delivery_carrier_label_roulier.product_product_dummy').id
        dummy_carrier = self.env.ref(
            'delivery_carrier_label_roulier.delivery_carrier_dummy').id
        carrier = False
        if is_dummy:
            carrier = dummy_carrier

        customer = self.env['res.partner'].search([], limit=1)
        order = self._create_order(customer, carrier)
        self._create_order_line(order, products)
        order.action_button_confirm()
        picking = order.picking_ids
        picking.do_transfer()
        return picking

    def test_dummy_example(self):
        """Ensure tests are running."""
        self.assertEqual(False, False)

    def test_implemented_by_carrier(self):
        """It should use the specific func when appropriated."""
        # we need to have weigths on product
        # because there is some get_weight on the list
        products = self._get_products([1])
        dummy_picking = self._generate_picking(products)
        other_picking = self._generate_picking(products, False)

        # ensure we get the specific function
        # in python 2.x we can't have the decorated function
        # but get only the decorator
        # (in python 3.x there is inspect.unwrap())
        #
        # Not a real good method, but it's ok to test the returned result

        # we test on _is_our wich returns true on roulier implementations
        # and false on the others

        self.assertEqual(
            dummy_picking._is_our(),
            True)

        self.assertEqual(
            dummy_picking._is_our(),
            dummy_picking._dummy_is_our())

        self.assertNotEqual(
            dummy_picking._is_our(),
            dummy_picking._roulier_is_our())

        self.assertNotEqual(
            dummy_picking._is_our(),
            other_picking._is_our())

        self.assertEqual(  # transitivity bro !
            other_picking._is_our(),
            other_picking._roulier_is_our())

        # ensure we have also generic functions too
        # both should call the same parent function
        self.assertEqual(
            dummy_picking._get_account(),
            other_picking._get_account())

    def test_generate_shipping_labels_one_package_implicit(self):
        """It should create 1 label if there is no packages."""
        products = self._get_products([1, 2, 3])
        picking = self._generate_picking(products)

        labels = picking.generate_shipping_labels()
        # dummy create one label per picking
        print "labels: ", labels
        self.assertEqual(len(labels), 1)

    def test_generate_shipping_labels_one_package_explicit(self):
        """It should create 1 label if there is 1 packages."""
        products = self._get_products([1, 2, 3])
        picking = self._generate_picking(products)
        package = self.env['stock.quant.package'].create({})

        operations = []
        for idx, product in enumerate(products):
            operations.append(self._create_operation(picking, {
                'product_qty': 1,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'result_package_id': package.id,
            }))

        labels = picking.generate_shipping_labels()
        self.assertEqual(len(labels), 1)

    def test_generate_shipping_labels_all_packages(self):
        """It should create many label as packages."""
        products = self._get_products([1, 2, 3])
        picking = self._generate_picking(products)

        packages = [
            self.env['stock.quant.package'].create({}),
            self.env['stock.quant.package'].create({})
        ]

        operations = []
        for idx, product in enumerate(products):
            operations.append(self._create_operation(picking, {
                'product_qty': 1,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'result_package_id': packages[idx % len(packages)].id,
            }))

        # dummy create one label per package
        labels = picking.generate_shipping_labels()
        self.assertEqual(len(labels), len(packages))

    def test_generate_shipping_labels_some_packages(self):
        """It should use package_ids instead of self."""
        products = self._get_products([1, 2, 3])
        picking = self._generate_picking(products)

        packages = [
            self.env['stock.quant.package'].create({}),
            self.env['stock.quant.package'].create({})
        ]

        operations = []
        for idx, product in enumerate(products):
            operations.append(self._create_operation(picking, {
                'product_qty': 1,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'result_package_id': packages[idx % len(packages)].id,
            }))

        # dummy create one label per package
        package_ids = [packages[0]]
        labels = picking.generate_shipping_labels(package_ids)
        self.assertEqual(len(labels), len(package_ids))  # =1
