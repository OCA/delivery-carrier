# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, fields, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    invoice_policy = fields.Selection(related="carrier_id.invoice_policy")

    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if result.get("type") == "form":
            result["arch"] = self._fields_view_get_adapt_attrs(result["arch"])
        return result

    def _fields_view_get_adapt_attrs(self, view_arch):
        doc = etree.XML(view_arch)
        # hide this button for delivery providers which have already
        # an attrs with a domain we can't extend...
        self.env["delivery.carrier"]._add_pricelist_domain(
            doc, "//button[@name='update_price']", "invisible"
        )
        return etree.tostring(doc, encoding="unicode")

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        self.delivery_message = False
        if "pricelist" in (self.delivery_type, self.invoice_policy):
            vals = self._get_shipment_rate()
            if vals.get("error_message"):
                return {"error": vals["error_message"]}
        else:
            return super()._onchange_carrier_id()

    @api.onchange("order_id")
    def _onchange_order_id(self):
        # pricelist delivery price will be computed on each carrier change so
        # no need to recompute here
        if "pricelist" not in (self.delivery_type, self.invoice_policy):
            return super()._onchange_order_id()
