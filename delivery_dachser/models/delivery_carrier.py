# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import _, fields, models
from odoo.exceptions import UserError

from .dachser_master_data import (
    DACHSER_BASKETS,
    DACHSER_COLLECTION_OPTIONS,
    DACHSER_DELIVERY_NOTICE_TYPES,
    DACHSER_DIVISIONS,
    DACHSER_LABEL_FORMATS,
    DACHSER_LABEL_TYPES,
    DACHSER_LOGISTICS_TYPES,
    DACHSER_OPERATION_MODES,
    DACHSER_PACKAGING_F,
    DACHSER_PACKAGING_T,
    DACHSER_PRODUCTS_F,
    DACHSER_PRODUCTS_T,
    DACHSER_TERMS,
    DACHSER_TRACKING_URL_TEMPLATE,
)
from .dachser_request import DachserRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("dachser", "Dachser")],
        ondelete={"dachser": "set default"},
    )

    # Connection & Shipper Identification
    dachser_api_key = fields.Char(
        copy=False,
        groups="base.group_system",
        help="X-API-Key token from Dachser API Portal (test or production).",
    )
    dachser_client_id = fields.Char(
        string="Dachser IBM Client ID",
        copy=False,
        groups="base.group_system",
        help="Optional X-IBM-Client-Id header if required by your Dachser account.",
    )
    dachser_forwarder_id = fields.Char(
        string="Dachser Branch ID",
        default="193",
        help="3-digit Dachser branch code handling collections (e.g. 193).",
    )
    dachser_consignor_id = fields.Char(
        string="Dachser Customer ID",
        help="8-digit customer/shipper account number assigned by Dachser.",
    )
    dachser_consignor_gln = fields.Char(
        string="Dachser Shipper GLN",
        size=13,
        help="Optional 13-digit Global Location Number of the shipper.",
    )

    # Division, Product, Terms & Packaging
    dachser_division = fields.Selection(
        selection=DACHSER_DIVISIONS,
        default="T",
    )
    dachser_product_t = fields.Selection(
        selection=DACHSER_PRODUCTS_T,
        default="Y",
        string="Dachser Product (T)",
    )
    dachser_product_f = fields.Selection(
        selection=DACHSER_PRODUCTS_F,
        default="N",
        string="Dachser Product (F)",
    )
    dachser_term = fields.Selection(
        selection=DACHSER_TERMS,
        default="031",
    )
    dachser_use_order_incoterm = fields.Boolean(
        string="Map Dachser Term from Incoterm",
        default=True,
        help=(
            "If enabled and the order/picking has an Incoterm (EXW, FCA, DAP, DDP...), "
            "automatically map it to the corresponding Dachser 3-digit term code."
        ),
    )
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
        string="Dachser Default Packaging",
        domain=[("package_carrier_type", "=", "dachser")],
        help="Default weight, height, width and length for Dachser packages.",
    )
    dachser_default_content = fields.Char(
        default="Goods",
        size=20,
        help="Default goods description sent on transportOrderLines (max 20 chars).",
    )

    # Workflow, Labels & Transport Options
    dachser_operation_mode = fields.Selection(
        selection=DACHSER_OPERATION_MODES,
        default="transportorder",
    )
    dachser_basket = fields.Selection(
        selection=DACHSER_BASKETS,
        default="sent",
        help="Target eLogistics basket when creating transport orders.",
    )
    dachser_label_format = fields.Selection(
        selection=DACHSER_LABEL_FORMATS,
        default="P",
        help="P = Ready-to-print PDF; Z = ZPL for Zebra thermal printers.",
    )
    dachser_label_types = fields.Selection(
        selection=DACHSER_LABEL_TYPES,
        default="EAN",
    )
    dachser_font_file_name = fields.Char(
        default="ARIALR.FNT",
        help="Zebra printer font file name required when using ZPL format.",
    )
    dachser_order_group = fields.Char(
        size=30,
        help="Optional order group name in eLogistics for Transfer Lists.",
    )
    dachser_logistics_type = fields.Selection(
        selection=DACHSER_LOGISTICS_TYPES,
        default="D",
    )
    dachser_save_quotation = fields.Boolean(default=False)
    dachser_collection_option = fields.Selection(
        selection=DACHSER_COLLECTION_OPTIONS,
        default="CN",
    )
    dachser_collection_time_from = fields.Char(
        help="Collection window start time in HH:MM format (e.g. 09:00).",
    )
    dachser_collection_time_to = fields.Char(
        help="Collection window end time in HH:MM format (e.g. 17:00).",
    )
    dachser_delivery_tail_lift = fields.Boolean(default=False)
    dachser_delivery_notice_type = fields.Selection(
        selection=DACHSER_DELIVERY_NOTICE_TYPES,
        default="none",
    )
    dachser_self_collector = fields.Boolean(default=False)
    dachser_frost_protected = fields.Boolean(default=False)

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------
    def _dachser_convert_price(self, amount, currency_code, currency, company, date):
        if currency_code and currency and currency_code != currency.name:
            src_currency = self.env["res.currency"].search(
                [("name", "=", currency_code)], limit=1
            )
            if src_currency:
                return src_currency._convert(
                    amount,
                    currency,
                    company or self.env.company,
                    date or fields.Date.context_today(self),
                )
        return amount

    def _dachser_create_label_attachment(
        self, picking, label_b64, tracking_ref, is_return=False
    ):
        self.ensure_one()
        if not label_b64:
            return False
        ext = "zpl" if self.dachser_label_format == "Z" else "pdf"
        mimetype = "text/plain" if ext == "zpl" else "application/pdf"
        prefix = "dachser_return" if is_return else "dachser_label"
        safe_ref = str(tracking_ref or picking.name or "shipment").replace("/", "_")
        raw_bytes = (
            base64.b64decode(label_b64)
            if isinstance(label_b64, str | bytes)
            else label_b64
        )
        return (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": f"{prefix}_{safe_ref}.{ext}",
                    "datas": base64.b64encode(raw_bytes),
                    "type": "binary",
                    "res_model": picking._name,
                    "res_id": picking.id,
                    "mimetype": mimetype,
                }
            )
        )

    # -------------------------------------------------------------------------
    # Odoo / OCA Delivery Carrier Hooks
    # -------------------------------------------------------------------------
    def dachser_rate_shipment(self, order):
        self.ensure_one()
        response = DachserRequest(self).rate_shipment(order)
        if not response["success"]:
            return {
                "success": False,
                "price": 0.0,
                "error_message": response["error_message"],
                "warning_message": False,
            }
        price = self._dachser_convert_price(
            response["price"],
            response["currency"],
            order.currency_id,
            order.company_id,
            order.date_order,
        )
        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": False,
        }

    def dachser_send_shipping(self, pickings):
        self.ensure_one()
        dachser_request = DachserRequest(self)
        result = []
        for picking in pickings:
            response = dachser_request.send_shipping(picking)
            ssccs = response.get("ssccs") or []
            packages = picking.move_line_ids.mapped("result_package_id")
            for idx, pkg in enumerate(packages):
                if idx < len(ssccs):
                    pkg.dachser_sscc = ssccs[idx]

            meta = (
                dict(picking.tracking_json)
                if isinstance(picking.tracking_json, dict)
                else {}
            )
            meta.update(
                {
                    "transport_order_id": response.get("order_id"),
                    "order_state": response.get("state"),
                    "ssccs": ssccs,
                    "ldr_routing": response.get("ldr_routing"),
                }
            )
            vals = {
                "delivery_state": "shipping_recorded_in_carrier",
                "tracking_state_history": response.get("state") or "sent",
                "tracking_json": meta,
            }
            if not picking.number_of_packages and ssccs:
                vals["number_of_packages"] = len(ssccs)
            picking.write(vals)

            if response.get("label"):
                self._dachser_create_label_attachment(
                    picking, response["label"], response["tracking_number"]
                )
            result.append(
                {
                    "tracking_number": response["tracking_number"],
                    "exact_price": 0.0,
                }
            )
        return result

    def dachser_get_label(self, picking):
        self.ensure_one()
        response = DachserRequest(self).get_label(picking)
        ssccs = response.get("ssccs") or []
        if ssccs and not picking.carrier_tracking_ref:
            picking.carrier_tracking_ref = ", ".join(ssccs)
        ref = ssccs[0] if ssccs else (picking.carrier_tracking_ref or picking.name)
        attachment = self._dachser_create_label_attachment(
            picking, response.get("label"), ref
        )
        if attachment:
            picking.message_post(
                body=_("Dachser label downloaded."),
                attachment_ids=[attachment.id],
            )
        return attachment

    def dachser_send_order_to_tms(self, picking):
        self.ensure_one()
        meta = (
            dict(picking.tracking_json)
            if isinstance(picking.tracking_json, dict)
            else {}
        )
        order_id = meta.get("transport_order_id")
        if not order_id:
            raise UserError(
                _("Picking %s does not have a pending Dachser Transport Order ID.")
                % picking.name
            )
        response = DachserRequest(self).send_transport_order(order_id)
        new_state = response.get("state") or "sent"
        ssccs = response.get("ssccs") or meta.get("ssccs") or []
        meta.update({"order_state": new_state, "ssccs": ssccs})
        vals = {
            "tracking_state_history": new_state,
            "tracking_json": meta,
        }
        if ssccs and (
            not picking.carrier_tracking_ref
            or picking.carrier_tracking_ref == str(order_id)
        ):
            vals["carrier_tracking_ref"] = ", ".join(ssccs)
        picking.write(vals)
        if response.get("label"):
            self._dachser_create_label_attachment(
                picking,
                response["label"],
                picking.carrier_tracking_ref or order_id,
            )
        return True

    def dachser_get_return_label(
        self, pickings, tracking_number=None, origin_date=None
    ):
        self.ensure_one()
        dachser_request = DachserRequest(self)
        for picking in pickings:
            response = dachser_request.get_return_label(
                picking, origin_date=origin_date
            )
            ssccs = response.get("ssccs") or []
            ref = ssccs[0] if ssccs else (tracking_number or picking.name)
            attachment = self._dachser_create_label_attachment(
                picking, response.get("label"), ref, is_return=True
            )
            if attachment:
                picking.message_post(
                    body=_("Dachser return label generated (SSCC: %s).") % ref,
                    attachment_ids=[attachment.id],
                )
        return True

    def dachser_get_tracking_link(self, picking):
        self.ensure_one()
        raw_ref = picking.carrier_tracking_ref or picking.name
        first_ref = str(raw_ref).split(",")[0].strip() if raw_ref else picking.name
        lang_code = picking.partner_id.lang or self.env.user.lang or "es_ES"
        if "_" not in lang_code:
            lang_code = "es_ES"
        return DACHSER_TRACKING_URL_TEMPLATE.format(
            lang=lang_code, tracking_ref=first_ref
        )

    def dachser_tracking_state_update(self, picking):
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        response = DachserRequest(self).get_tracking(picking)
        if not response["delivery_state"]:
            return
        vals = {
            "delivery_state": response["delivery_state"],
            "tracking_state": response["tracking_state"],
            "tracking_state_history": response["tracking_state_history"],
            "tracking_json": response["tracking_json"],
        }
        if (
            response["delivery_state"] == "customer_delivered"
            and not picking.date_delivered
        ):
            vals["date_delivered"] = fields.Datetime.now()
        if response.get("pod"):
            pod_data = response["pod"]
            vals.update(
                {
                    "pod_file": pod_data.encode("ascii")
                    if isinstance(pod_data, str)
                    else pod_data,
                    "pod_filename": response["pod_filename"],
                    "pod_error": False,
                }
            )
        picking.write(vals)

    def dachser_cancel_shipment(self, pickings):
        self.ensure_one()
        dachser_request = DachserRequest(self)
        cancel_error = _(
            "It is not possible to cancel a shipment because it has already been sent."
        )
        for picking in pickings.filtered("carrier_tracking_ref"):
            meta = (
                dict(picking.tracking_json)
                if isinstance(picking.tracking_json, dict)
                else {}
            )
            if meta.get("order_state") == "sent":
                raise UserError(cancel_error)
            order_ref = meta.get("transport_order_id") or picking.carrier_tracking_ref
            if not dachser_request.cancel_shipping(order_ref):
                raise UserError(cancel_error)
            meta["order_state"] = "cancelled"
            picking.write(
                {
                    "carrier_tracking_ref": False,
                    "delivery_state": "canceled_shipment",
                    "tracking_state_history": False,
                    "tracking_json": meta,
                }
            )
        return True

    def action_open_transfer_list_wizard(self):
        self.ensure_one()
        return {
            "name": _("Download Dachser Daily Manifest (Transfer List)"),
            "type": "ir.actions.act_window",
            "res_model": "dachser.transfer.list.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_carrier_id": self.id,
                "default_order_group": self.dachser_order_group or False,
            },
        }
