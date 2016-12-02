# -*- coding: utf-8 -*-

from openerp.tests.common import TransactionCase
from openerp.exceptions import Warning as UserError


class TestDummy(TransactionCase):
    """Test dumy functions."""

    def setUp(self):
        super(TestDummy, self).setUp()
        self.products = self.env.ref('delivery_roulier.product_dummy_small')
        self.products |= self.env.ref('delivery_roulier.product_dummy_normal')
        self.products |= self.env.ref('delivery_roulier.product_dummy_big')

    # some helpers
    def _create_sale(self, customer, carrier=None):
        vals = {
            'partner_id': customer.id,
        }
        if carrier:
            vals['carrier_id'] = carrier
        return self.env['sale.order'].create(vals)

    def _create_sale_line(self, sale, products):
        ol = []
        for product in products:
            ol.append(self.env['sale.order.line'].create({
                'product_id': product.id,
                'order_id': sale.id,
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

    def _generate_picking(self, products, is_dummy=True):
        """Create a picking from products."""
        dummy_carrier = self.env.ref(
            'delivery_roulier.delivery_carrier_dummy').id
        carrier = False
        if is_dummy:
            carrier = dummy_carrier

        customer = self.env['res.partner'].search([], limit=3)[2]
        sale = self._create_sale(customer, carrier)
        self._create_sale_line(sale, products)
        sale.action_button_confirm()
        picking = sale.picking_ids
        picking.do_transfer()
        return picking

    def test_dummy_example(self):
        """Ensure tests are running."""
        self.assertEqual(False, False)

    def test_is_roulier(self):
        """It should return true when handled."""
        # we need to have weigths on product
        # because there is some get_weight on the list

        dummy_picking = self._generate_picking(self.products)
        other_picking = self._generate_picking(self.products, False)

        # ensure we get the specific function
        # in python 2.x we can't have the decorated function
        # but get only the decorator
        # (in python 3.x there is inspect.unwrap())
        #
        # Not a real good method, but it's ok to test the returned result

        # _is_roulier which returns true on roulier implementations
        # and false on the others

        self.assertEqual(
            dummy_picking._is_roulier(),
            True)

        # btw is_roulier should work only on roulier' managed pickings
        self.assertNotEqual(
            dummy_picking._is_roulier(),
            other_picking._is_roulier())

    def test_generate_shipping_labels_no_package(self):
        """It should fail because there is no package."""
        picking = self._generate_picking(self.products)

        try:
            labels = picking.generate_labels()
        except UserError:
            self.assertTrue(True)
            return
        # when automatic package creation will be there
        # test will be:
        self.assertEqual(len(labels), 1)
        return True

    def test_generate_shipping_labels_one_package_explicit(self):
        """It should create 1 label if there is 1 package."""
        picking = self._generate_picking(self.products)
        package = self.env['stock.quant.package'].create({})

        operations = []
        for idx, product in enumerate(self.products):
            operations.append(self._create_operation(picking, {
                'product_qty': 1,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'result_package_id': package.id,
            }))
        packages = picking._get_packages_from_picking()
        labels = packages._generate_labels(picking)
        self.assertEqual(len(labels), 1)

    def test_generate_shipping_labels_all_packages(self):
        """It should create many label as packages."""
        picking = self._generate_picking(self.products)

        packages = [
            self.env['stock.quant.package'].create({}),
            self.env['stock.quant.package'].create({})
        ]

        operations = []
        for idx, product in enumerate(self.products):
            operations.append(self._create_operation(picking, {
                'product_qty': 1,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'result_package_id': packages[idx % len(packages)].id,
            }))

        # dummy create one label per package
        labels = picking.generate_labels()
        self.assertEqual(len(labels), len(packages))

    def test_generate_shipping_labels_some_packages(self):
        """It should use self instead of package_ids."""
        picking = self._generate_picking(self.products)

        packages = [
            self.env['stock.quant.package'].create({}),
            self.env['stock.quant.package'].create({})
        ]

        operations = []
        for idx, product in enumerate(self.products):
            operations.append(self._create_operation(picking, {
                'product_qty': 1,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'result_package_id': packages[idx % len(packages)].id,
            }))

        # dummy create one label per package
        package_ids = [packages[0]]

        labels = picking.generate_labels(package_ids)
        self.assertNotEqual(len(labels), len(package_ids))  # =1
