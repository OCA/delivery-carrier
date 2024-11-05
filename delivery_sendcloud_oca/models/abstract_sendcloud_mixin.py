# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import api, fields, models


class SendcloudMixin(models.AbstractModel):
    _name = "sendcloud.mixin"
    _description = "Sendcloud Mixin Abstract"

    is_sendcloud_test_mode = fields.Boolean(compute="_compute_is_sendcloud_test_mode")

    def _sendcloud_convert_weight_to_kg(self, weight):
        uom = self.env["product.template"]._get_weight_uom_id_from_ir_config_parameter()
        uom_kgm = self.env.ref("uom.product_uom_kgm")
        amount = uom._compute_quantity(weight, uom_kgm, round=True)
        return round(amount, 2)  # Force round as sometimes odoo fails to round properly

    @api.model
    def _get_sendcloud_customs_shipment_type(self):
        return [
            ("0", "Gift"),
            ("1", "Documents"),
            ("2", "Commercial Goods"),
            ("3", "Commercial Sample"),
            ("4", "Returned Goods"),
        ]

    @api.model
    def _default_get_sendcloud_customs_shipment_type(self):
        return "2"

    def _compute_is_sendcloud_test_mode(self):
        for record in self:
            record.is_sendcloud_test_mode = self.env.company.is_sendcloud_test_mode
