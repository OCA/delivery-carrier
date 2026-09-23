#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
    from roulier.exception import CarrierError, InvalidApiInput
except ImportError:
    _logger.debug("Cannot `import roulier`.")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _fedex_rest_get_shipping_date(self, package=None):
        shipping_date = fields.Date.context_today(self)
        while shipping_date.weekday() >= 5:
            shipping_date += timedelta(days=1)
        return shipping_date

    def _fedex_rest_get_service(self, account, package=None):
        service = self._roulier_get_service(account, package=package)
        service.update(
            {
                "accountNumber": account.fedex_rest_account_number or "",
                "labelStockType": account.fedex_rest_label_stock_type,
                "pickupType": account.fedex_rest_pickup_type,
                "etd": account.fedex_rest_use_etd,
                "reference1": self.sale_id.name or self.origin or self.name,
                "reference2": self.sale_id.client_order_ref or "",
            }
        )
        return service

    def _fedex_rest_convert_address(self, partner):
        address = self._roulier_convert_address(partner)
        if partner.state_id:
            address["state"] = partner.state_id.code
        address["residential"] = not partner.commercial_partner_id.is_company
        return address

    def _fedex_rest_convert_weight(self, weight):
        weight_uom = self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter()
        if weight_uom == self.env.ref("uom.product_uom_lb"):
            return weight, "LB"
        return (
            weight_uom._compute_quantity(weight, self.env.ref("uom.product_uom_kgm")),
            "KG",
        )

    def _fedex_rest_needs_customs(self):
        self.ensure_one()
        origin = self._get_sender().country_id
        destination = self._get_receiver().country_id
        if origin == destination:
            return False
        europe = self.env.ref("base.europe").country_ids
        return not (origin in europe and destination in europe)

    def _fedex_rest_get_customs(self, account, packages):
        self.ensure_one()
        move_lines = self.env["stock.move.line"].search(
            [
                ("picking_id", "=", self.id),
                ("result_package_id", "in", packages.ids),
                ("qty_done", ">", 0),
            ]
        )
        currency = self.sale_id.currency_id or self.company_id.currency_id
        _weight, weight_unit = self._fedex_rest_convert_weight(0.0)
        return {
            "currency": currency.name,
            "weightUnit": weight_unit,
            "dutiesPaymentType": account.fedex_rest_duties_payment_type,
            "incoterm": self.sale_id.incoterm.code or "",
            "commodities": [line._fedex_rest_get_commodity() for line in move_lines],
        }

    def _fedex_rest_cancel_shipment(self):
        for picking in self.filtered("carrier_tracking_ref"):
            account = picking._get_account()
            payload = {
                "auth": picking._get_auth(account),
                "shipment": {
                    "accountNumber": account.fedex_rest_account_number or "",
                    "trackingNumber": picking.carrier_tracking_ref.split(";")[0],
                },
            }
            try:
                result = roulier.get("fedex_rest", "cancel_shipment", payload)
            except (InvalidApiInput, CarrierError) as error:
                raise UserError(
                    _(
                        "FedEx shipment %(tracking)s could not be cancelled:\n%(error)s",
                        tracking=payload["shipment"]["trackingNumber"],
                        error=error,
                    )
                ) from error
            if not result.get("cancelled"):
                raise UserError(
                    _(
                        "FedEx refused to cancel shipment %s.",
                        payload["shipment"]["trackingNumber"],
                    )
                )
        return self._roulier_cancel_shipment()
