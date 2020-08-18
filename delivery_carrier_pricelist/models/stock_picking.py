# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from lxml import etree

from odoo import models
from odoo.osv import expression


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if result.get("name") == "stock.picking.form":
            result["arch"] = self._fields_view_get_adapt_attrs(result["arch"])
        return result

    def _fields_view_get_adapt_attrs(self, view_arch):
        doc = etree.XML(view_arch)
        # hide all these fields and buttons for delivery providers which have already
        # an attrs with a domain we can't extend...
        self.env["delivery.carrier"]._add_pricelist_domain(
            doc, "//button[@name='cancel_shipment']", "invisible"
        )
        self.env["delivery.carrier"]._add_pricelist_domain(
            doc, "//button[@name='send_to_shipper']", "invisible"
        )
        self.env["delivery.carrier"]._add_pricelist_domain(
            doc,
            "//field[@name='partner_id']",
            "required",
            domain_operator=expression.AND,
            field_operator="!=",
        )
        return etree.tostring(doc, encoding="unicode")
