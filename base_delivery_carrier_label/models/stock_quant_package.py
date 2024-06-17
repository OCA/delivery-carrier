# Copyright 2014-2015 Akretion <http://www.akretion.com>
# Copyright 2014-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    parcel_tracking = fields.Char()
    parcel_tracking_uri = fields.Char(
        help="Link to the carrier's tracking page for this package."
    )

    @api.depends("shipping_weight", "quant_ids", "package_type_id")
    def _compute_weight(self):
        """Use shipping_weight if defined
        otherwise fallback on the computed weight
        """
        to_do = self.browse()
        for pack in self:
            if pack.shipping_weight:
                pack.weight = pack.shipping_weight
            elif pack.quant_ids and not self.env.context.get("picking_id"):
                # package.pack_operations would be too easy
                operations = self.env["stock.move.line"].search(
                    [
                        ("result_package_id", "=", pack.id),
                        ("package_id", "=", False),
                        ("product_id", "!=", False),
                    ]
                )

                pack.weight = operations.get_weight()
            else:
                to_do |= pack
        if to_do:
            return super(StockQuantPackage, to_do)._compute_weight()

    def _complete_name(self, name, args):
        res = super()._complete_name(name, args)
        for pack in self:
            if pack.parcel_tracking:
                res[pack.id] += " [%s]" % pack.parcel_tracking
            if pack.weight:
                res[pack.id] += " %s kg" % pack.weight
        return res

    def open_website_url(self):
        """Implement you own action in your module"""
        return None
