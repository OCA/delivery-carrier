# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    invoice_policy = fields.Selection(related="carrier_id.invoice_policy")

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(
            view_id=view_id, view_type=view_type, options=options
        )
        if view.type == "form":
            arch = self._fields_view_get_adapt_attrs(arch)
        return arch, view

    def _fields_view_get_adapt_attrs(self, view_arch):
        # hide this button for delivery providers which have already
        # an attrs with a domain we can't extend...
        self.env["delivery.carrier"]._add_pricelist_domain(
            view_arch, "//button[@name='update_price']", "invisible"
        )
        return view_arch

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        self.delivery_message = False
        if "pricelist" in (self.delivery_type, self.invoice_policy):
            vals = self._get_delivery_rate()
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
