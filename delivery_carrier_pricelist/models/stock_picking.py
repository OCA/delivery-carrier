# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(
            view_id=view_id, view_type=view_type, options=options
        )
        if view.name == "stock.picking.form":
            arch = self._fields_view_get_adapt_attrs(arch)
        return arch, view

    def _fields_view_get_adapt_attrs(self, view_arch):
        # hide all these fields and buttons for delivery providers which have already
        # an attrs with a domain we can't extend...
        self.env["delivery.carrier"]._add_pricelist_domain(
            view_arch, "//button[@name='cancel_shipment']", "invisible"
        )
        self.env["delivery.carrier"]._add_pricelist_domain(
            view_arch, "//button[@name='send_to_shipper']", "invisible"
        )
        self.env["delivery.carrier"]._add_pricelist_domain(
            view_arch,
            "//field[@name='partner_id']",
            "required",
            domain_operator="and",
            field_operator="!=",
        )
        return view_arch
