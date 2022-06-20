# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import _, api, fields, models

from .tnt_request import TntRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("tnt_oca", "TNT")])
    tnt_oca_ws_username = fields.Char(string="WS Username")
    tnt_oca_ws_password = fields.Char(string="WS Password")
    tnt_oca_ws_account = fields.Char(string="WS Account")
    # Misc
    tnt_product_type = fields.Selection(
        selection=[
            ("D", "Document (paper/manuals/reports)"),
            ("N", "Non-document (packages)"),
        ],
        default="N",
        string="Product type",
    )
    tnt_product_code = fields.Char(
        compute="_compute_tnt_product_code", string="Product code",
    )
    tnt_product_code_d = fields.Selection(
        selection=[
            ("09D", "9:00 EXPRESS"),
            ("12D", "12:00 EXPRESS"),
            ("15D", "GLOBAL EXPRESS"),
        ],
        default="09D",
        string="Product code (Docs)",
    )
    tnt_product_code_n = fields.Selection(
        selection=[("15N", "GLOBAL EXPRESS"), ("48N", "ECONOMY EXPRESS")],
        default="15N",
        string="Product code (Non docs)",
    )
    tnt_product_service = fields.Char(
        compute="_compute_tnt_product_service", string="Product service",
    )
    tnt_product_service_d = fields.Selection(
        selection=[
            ("EX", "Express"),
            ("EX09", "9:00 Express"),
            ("EX10", "10:00 Express"),
            ("EX12", "12:00 Express"),
        ],
        default="EX",
        string="Product service (Docs)",
    )
    tnt_product_service_n = fields.Selection(
        selection=[
            ("EC", "Economy Express"),
            ("EC12", "12:00 Economy Express"),
            ("EX", "Express"),
            ("EX09", "9:00 Express"),
            ("EX10", "10:00 Express"),
            ("EX12", "12:00 Express"),
        ],
        default="EX",
        string="Product service (Non docs)",
    )
    tnt_payment_indicator = fields.Selection(
        selection=[("S", "Sender pays"), ("R", "Receiver pays")],
        default="S",
        string="Payment indicator",
    )
    tnt_line_of_business = fields.Selection(
        selection=[
            ("1", "Domestic transfers"),
            ("2", "International non-domestic transfers"),
        ],
        default="1",
        string="Line of business",
    )
    tnt_collect_time_from = fields.Float(default=10.5, string="Collect time from")
    tnt_collect_time_to = fields.Float(default=16, string="Collect time to")
    tnt_default_packaging_id = fields.Many2one(
        comodel_name="product.packaging",
        string="Default Packaging Type",
        domain=[("package_carrier_type", "=", "tnt_oca")],
    )

    @api.depends("delivery_type", "tnt_product_type")
    def _compute_tnt_product_code(self):
        for item in self:
            if item.delivery_type == "tnt_oca":
                if item.tnt_product_type == "D":
                    item.tnt_product_code = item.tnt_product_code_d
                else:
                    item.tnt_product_code = item.tnt_product_code_n
            else:
                item.tnt_product_code = item.tnt_product_code

    @api.depends("delivery_type", "tnt_product_type")
    def _compute_tnt_product_service(self):
        for item in self:
            if item.delivery_type == "tnt_oca":
                if item.tnt_product_type == "D":
                    item.tnt_product_service = item.tnt_product_service_d
                else:
                    item.tnt_product_service = item.tnt_product_service_n
            else:
                item.tnt_product_service = item.tnt_product_service

    def tnt_oca_rate_shipment(self, order):
        tnt_request = TntRequest(self, order)
        response = tnt_request.rate_shipment()
        if response["success"]:
            response["price"] = self._tnt_oca_get_response_price(
                response, order.currency_id, order.company_id
            )
        return {
            "success": response["success"],
            "price": response["price"],
            "error_message": False,
            "warning_message": False,
        }

    def _tnt_oca_get_response_price(self, response, currency, company):
        """We need to convert the price if the currency is different."""
        price = float(response["price"])
        if response["currency"] != currency.name:
            price = currency._convert(
                price,
                self.env["res.currency"].search([("name", "=", response["currency"])]),
                company,
                fields.Date.today(),
            )
        return price

    def _tnt_oca_action_label(self, picking):
        report_name = "delivery_tnt_oca.label_delivery_tnt_oca_template"
        iar = self.env["ir.actions.report"]
        res = iar._get_report_from_name(report_name).render_qweb_text(picking.ids)
        return self.env["ir.attachment"].create(
            {
                "name": "TNT-%s.txt" % picking.carrier_tracking_ref,
                "type": "binary",
                "datas": base64.b64encode(res[0]),
                "res_model": picking._name,
                "res_id": picking.id,
            }
        )

    def tnt_oca_send_shipping(self, pickings):
        return [self.tnt_oca_create_shipping(p) for p in pickings]

    def tnt_oca_create_shipping(self, picking):
        self.ensure_one()
        tnt_request = TntRequest(self, picking)
        tnt_request._send_shipping()
        tnt_request._get_label_info()
        self._tnt_oca_action_label(picking)
        return {
            "exact_price": 0,
            "tracking_number": picking.carrier_tracking_ref,
        }

    def tnt_oca_tracking_state_update(self, picking):
        self.ensure_one()
        if picking.carrier_tracking_ref:
            tnt_request = TntRequest(self, picking)
            response = tnt_request.tracking_state_update()
            picking.delivery_state = response["delivery_state"]
            picking.tracking_state_history = response["tracking_state_history"]

    def tnt_oca_cancel_shipment(self, pickings):
        raise NotImplementedError(
            _("""TNT API does not allow you to cancel a shipment.""")
        )

    def tnt_oca_get_tracking_link(self, picking):
        return "%s/%s?searchType=con&cons=%s" % (
            "https://www.tnt.com",
            "express/es_es/site/herramientas-envio/seguimiento.html",
            picking.carrier_tracking_ref,
        )
