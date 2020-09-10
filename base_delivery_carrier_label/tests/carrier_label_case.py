# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class CarrierLabelCase(TransactionCase):
    """Base class for carrier label tests. Inherit and override _get_carrier
    to return the carrier you want to test"""

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self._create_order_picking()

    def _create_order_picking(self):
        """Create a sale order and deliver the picking"""
        self.order = self.env["sale.order"].create(self._sale_order_data())
        self.order.action_confirm()
        self.picking = self.order.picking_ids
        self.picking.action_done()

    def _get_carrier(self):
        """Return the carrier to test"""
        raise NotImplementedError()

    def _sale_order_data(self):
        """Return a values dict to create a sale order"""
        return {
            "partner_id": self.env["res.partner"].create(self._partner_data()).id,
            "order_line": [(0, 0, data) for data in self._order_line_data()],
            "carrier_id": self._get_carrier().id,
        }

    def _partner_data(self):
        """Return a values dict to create a partner"""
        return {
            "name": "Carrier label test customer",
            "customer": True,
        }

    def _order_line_data(self):
        """Return a list of value dicts to create order lines"""
        return [
            {"product_id": self.env["product.product"].create(self._product_data()).id}
        ]

    def _product_data(self):
        """Return a values dict to create a product"""
        return {
            "name": "Carrier test product",
            "type": "product",
        }

    def _assert_labels(self):
        """Fail if there are no labels for the current picking"""
        try:
            self.picking._check_existing_shipping_label()
        except UserError:
            return
        self.fail("No labels found")

    def test_labels(self):
        """Test if labels are created by the button"""
        self.picking.action_generate_carrier_label()
        self._assert_labels()
