# Copyright 2016 Hpar
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models
from odoo.tools import float_round


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    weight = fields.Float(digits="Stock Weight")

    def get_weight(self):
        prec = self.env["decimal.precision"].precision_get("Stock Weight")
        weight_uom_categ_id = self.env.ref("uom.product_uom_categ_kgm").id
        ref_weight_uom = self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter()
        total_weight = 0.0
        for line in self:
            product = line.product_id
            if line.product_uom_id.category_id.id == weight_uom_categ_id:
                total_weight += line.product_uom_id._compute_quantity(
                    line.qty_done, ref_weight_uom, round=False
                )
            else:
                total_weight += (
                    line.product_uom_id._compute_quantity(
                        line.qty_done, product.uom_id, round=False
                    )
                    * product.weight
                )
        return float_round(total_weight, precision_digits=prec)
