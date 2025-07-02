# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class Common(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpClassCarrier()
        cls.setUpClassPicking()

    @classmethod
    def _create_carrier(cls, name, **kwargs):
        carrier_product = cls.env["product.product"].create(
            {
                "name": f"product {name}",
                "type": "service",
            }
        )
        carrier_values = {"name": name, "product_id": carrier_product.id}
        carrier_values.update(kwargs)
        return cls.env["delivery.carrier"].create(carrier_values)

    @classmethod
    def setUpClassCarrier(cls):
        cls.carrier_no_restriction = cls._create_carrier("no restriction")
        cls.carrier_volume_restriction = cls._create_carrier(
            "volume restriction", max_volume=1
        )
        cls.carrier_weight_restriction = cls._create_carrier(
            "weight restriction", max_weight=1
        )

    @classmethod
    def setUpClassPicking(cls):
        picking_type = cls.env.ref("stock.picking_type_out")
        cls.product = cls.env["product.product"].create(
            {"name": "Furniture", "volume": 2, "weight": 2}
        )
        with Form(cls.env["stock.picking"]) as pick_form:
            pick_form.picking_type_id = picking_type
            with pick_form.move_ids_without_package.new() as move:
                move.product_id = cls.product
                move.product_uom_qty = 1
        cls.picking = pick_form.save()
