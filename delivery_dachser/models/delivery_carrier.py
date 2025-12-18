# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import fields, models
from odoo.exceptions import UserError

from .dachser_master_data import (
    DACHSER_PACKAGING_F,
    DACHSER_PACKAGING_T,
    DACHSER_PRODUCTS_F,
    DACHSER_PRODUCTS_T,
    DACHSER_TERMS,
)
from .dachser_request import DachserRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("dachser", "Dachser")],
        ondelete={"dachser": "set default"},
    )
    dachser_api_key = fields.Char()
    dachser_division = fields.Selection(
        selection=[
            ("T", "(T) European Logistics"),
            ("F", "(F) Food Logistics"),
        ],
        default="T",
    )
    dachser_product_t = fields.Selection(
        selection=DACHSER_PRODUCTS_T,
        default="Y",
        string="Dachser Product (T)",
    )
    dachser_product_f = fields.Selection(
        selection=DACHSER_PRODUCTS_F,
        string="Dachser Product (F)",
    )
    dachser_term = fields.Selection(selection=DACHSER_TERMS, default="031")
    dachser_packaging_t = fields.Selection(
        selection=DACHSER_PACKAGING_T,
        default="EU",
        string="Dachser Packaging (T)",
    )
    dachser_packaging_f = fields.Selection(
        selection=DACHSER_PACKAGING_F,
        default="EU",
        string="Dachser Packaging (F)",
    )
    dachser_default_packaging_id = fields.Many2one(
        comodel_name="stock.package.type",
        string="Default Packaging Type",
        domain=[("package_carrier_type", "=", "dachser")],
        help="Default weight, height, width and length for packages",
    )

    def dachser_rate_shipment(self, order):
        self.ensure_one()
        response = DachserRequest(self).rate_shipment(order)
        return {
            "success": True,
            "price": response["price"],
            "error_message": response["error_message"],
            "warning_message": False,
        }

    def dachser_send_shipping(self, pickings):
        dachser_request = DachserRequest(self)
        result = []
        for picking in pickings:
            response = dachser_request.send_shipping(picking)
            result.append(
                {
                    "tracking_number": response["tracking_number"],
                    "exact_price": 0,
                }
            )
            if response.get("label"):
                label = response.get("label")
                if isinstance(label, str):
                    datas = label
                else:
                    datas = base64.b64encode(label).decode("utf-8")
                self.env["ir.attachment"].sudo().create(
                    {
                        "name": "dachser.pdf",
                        "datas": datas,
                        "type": "binary",
                        "res_model": picking._name,
                        "res_id": picking.id,
                    }
                )
        return result

    def dachser_tracking_state_update(self, picking):
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        response = DachserRequest(self).get_tracking(picking.carrier_tracking_ref)
        picking.tracking_state = response["tracking_state"]
        picking.delivery_state = response["delivery_state"]
        picking.tracking_state_history = "\n".join(
            [
                "- {}: [{}] {}".format(
                    event["statusDate"], event["code"], event["description"]
                )
                for event in response["tracking_events"]
            ]
        )

    def dachser_cancel_shipment(self, pickings):
        for picking in pickings.filtered("carrier_tracking_ref"):
            response = DachserRequest(self).cancel_shipping(
                picking.carrier_tracking_ref
            )
            if not response:
                raise UserError(
                    self.env._(
                        "It is not possible to cancel a shipment because "
                        "it has already been sent."
                    )
                )
