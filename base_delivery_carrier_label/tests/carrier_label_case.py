# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class CarrierLabelCase(TransactionCase):
    """Base class for carrier label tests. Inherit and override _get_carrier
    to return the carrier you want to test"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_order_picking()

    @property
    def transfer_in_setup(self):
        return True

    @classmethod
    def _create_order_picking(cls):
        """Create a sale order and deliver the picking"""
        cls.order = cls.env["sale.order"].create(cls._sale_order_data())
        for product in cls.order.mapped("order_line.product_id"):
            cls.env["stock.quant"].with_context(inventory_mode=True).create(
                {
                    "product_id": product.id,
                    "location_id": cls.order.warehouse_id.lot_stock_id.id,
                    "inventory_quantity": sum(
                        cls.order.mapped("order_line.product_uom_qty")
                    ),
                }
            )._apply_inventory()
        cls.order.action_confirm()
        cls.picking = cls.order.picking_ids
        cls.picking.write(cls._picking_data())
        if cls.transfer_in_setup:
            cls._transfer_order_picking()

    @classmethod
    def _transfer_order_picking(cls):
        cls.env["stock.immediate.transfer"].create(
            {"pick_ids": [(6, 0, cls.picking.ids)]}
        ).process()

    @classmethod
    def _get_carrier(cls):
        """Return the carrier to test"""
        raise NotImplementedError()

    @classmethod
    def _sale_order_data(cls):
        """Return a values dict to create a sale order"""
        return {
            "partner_id": cls.env["res.partner"].create(cls._partner_data()).id,
            "order_line": [(0, 0, data) for data in cls._order_line_data()],
            "carrier_id": cls._get_carrier().id,
        }

    @classmethod
    def _partner_data(cls):
        """Return a values dict to create a partner"""
        return {
            "name": "Carrier label test customer",
        }

    @classmethod
    def _order_line_data(cls):
        """Return a list of value dicts to create order lines"""
        return [
            {
                "product_id": cls.env["product.product"].create(cls._product_data()).id,
                "product_uom_qty": 1,
            }
        ]

    @classmethod
    def _product_data(cls):
        """Return a values dict to create a product"""
        return {
            "name": "Carrier test product",
            "type": "product",
        }

    @classmethod
    def _picking_data(cls):
        """Return a values dict to be written to the picking in order to set
        carrier options"""
        return {}

    def _assert_labels(self):
        """Fail if there are no labels for the current picking"""
        try:
            self.picking._check_existing_shipping_label()
        except UserError:
            return
        self.fail("No labels found")


class TestCarrierLabel(CarrierLabelCase):
    def test_labels(self):
        """Test if labels are created by the button"""
        self.picking.send_to_shipper()
        self._assert_labels()
