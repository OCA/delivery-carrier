# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def _chronopost_fr_manage_options(self, picking, payload):
        # Set default values
        payload["to_address"]["preAlert"] = 0
        payload["from_address"]["preAlert"] = 0
        for option in picking.option_ids:
            if option.code == "INS":
                # Multi package label is not supported for now
                payload["parcels"][0]["insuredValue"] = self._get_sale_price(picking)
                curr = picking.sale_id.currency_id or picking.company_id.currency_id
                payload["service"]["insuredCurrency"] = curr.code
            if option.code == "MON":
                payload["service"]["service"] = "1"
            if option.code == "SAT":
                payload["service"]["service"] = "6"
            if option.code == "SHIPALERT":
                payload["from_address"]["preAlert"] = 11
            if option.code == "RECIPALERT":
                payload["from_address"]["preAlert"] = 22

    # could be generic in delivery_roulier_option ?
    def _chronopost_fr_before_call(self, picking, payload):
        self._chronopost_fr_manage_options(picking, payload)
        return payload

    def _get_chronopost_fr_object_type(self, picking):
        # Override it to implement a specific logic
        return "MAR"

    def _chronopost_fr_get_parcel(self, picking):
        vals = self._roulier_get_parcel(picking)
        vals["objectType"] = self._get_chronopost_fr_object_type(picking)
        # Manage options
        if self._should_include_customs(picking):
            vals["customsValue"] = self._get_sale_price(picking)
            curr = picking.sale_id.currency_id or picking.company_id.currency_id
            vals["insuredCurrency"] = curr.code
        return vals

    def _chronopost_fr_should_include_customs(self, picking):
        if picking.carrier_code == "chexp":
            return True
        return False
