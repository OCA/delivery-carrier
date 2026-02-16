# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _dhl_express_get_service(self, account, package=None):
        service = self._roulier_get_service(account, package=package)
        service.update(
            {
                "product": self.carrier_code,
                "customerId": account.dhl_express_account_number,
                "shipment_description": f"Shipment {self.name} from "
                f"{self.partner_id.name} from Odoo",
                "reference1": self.partner_id.name[:35]
                if self.partner_id.name
                else "/",
            }
        )
        return service

    @api.model
    def _dhl_express_convert_address(self, partner):
        address = self._roulier_convert_address(partner) or {}
        # Use get_split_adress from partner_helper module
        # to split the address on 3 lines
        streets = partner._get_split_address(3, 45)
        (
            address["street1"],
            address["street2"],
            address["street3"],
        ) = streets
        return address
