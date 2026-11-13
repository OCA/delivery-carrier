# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging
import math

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from . import dachser_master_data as _dmd
from .dachser_master_data import (
    DACHSER_BASKETS,
    DACHSER_COLLECTION_OPTIONS,
    DACHSER_DELIVERY_NOTICE_TYPES,
    DACHSER_DIVISIONS,
    DACHSER_INCOTERM_TO_TERM,
    DACHSER_LABEL_FORMATS,
    DACHSER_LABEL_TYPES,
    DACHSER_LOGISTICS_TYPES,
    DACHSER_OPERATION_MODES,
    DACHSER_PACKAGING_CODES,
    DACHSER_PACKAGING_F,
    DACHSER_PACKAGING_T,
    DACHSER_PRODUCTS,
    DACHSER_PRODUCTS_F,
    DACHSER_PRODUCTS_T,
    DACHSER_RATE_MODES,
    DACHSER_TERMS,
    map_dachser_status_to_delivery_state,
    map_dachser_status_to_state,
)
from .dachser_request import DachserRequest

DACHSER_DEFAULT_API_URL = getattr(
    _dmd,
    "DACHSER_DEFAULT_API_URL",
    getattr(
        _dmd, "DACHSER_DEFAULT_BASE_URL", "https://api-gateway.dachser.com/rest/v2"
    ),
)
DACHSER_TRACKING_URL_TEMPLATE = getattr(
    _dmd,
    "DACHSER_TRACKING_URL_TEMPLATE",
    "https://elogistics.dachser.com/shpdl/?l={lang}&c=10&n={tracking_ref}",
)

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("dachser", "Dachser")],
        ondelete={
            "dachser": lambda recs: recs.write(
                {"delivery_type": "fixed", "fixed_price": 0}
            )
        },
    )

    # =========================================================================
    # DACHSER REST API V2 CREDENTIALS & CONNECTION (OCA + ENHANCED)
    # =========================================================================
    dachser_api_url = fields.Char(
        string="Dachser API Base URL",
        default=DACHSER_DEFAULT_API_URL,
        help=(
            "Dachser API Gateway v2 base URL "
            "(default: https://api-gateway.dachser.com/rest/v2)."
        ),
    )
    dachser_api_key = fields.Char(
        string="Dachser API Key (X-API-Key)",
        copy=False,
        groups="base.group_system",
        help=(
            "Primary X-API-Key token for Dachser REST API v2 "
            "(used as fallback if environment-specific keys are empty)."
        ),
    )
    dachser_api_key_test = fields.Char(
        string="Test API Key (X-API-Key)",
        copy=False,
        groups="base.group_system",
        help=(
            "Test X-API-Key token (10-day self-service token from "
            "api-portal.dachser.com or QA token)."
        ),
    )
    dachser_api_key_prod = fields.Char(
        string="Production API Key (X-API-Key)",
        copy=False,
        groups="base.group_system",
        help="Production X-API-Key token provided by your Dachser branch.",
    )
    dachser_client_id = fields.Char(
        string="Additional Client ID (Optional)",
        copy=False,
        groups="base.group_system",
        help="Optional X-IBM-Client-Id header if required by your Dachser branch.",
    )
    dachser_forwarder_id = fields.Char(
        string="Dachser Branch ID (Forwarder ID)",
        default="193",
        help="3-digit code of the receiving Dachser branch (e.g. '193', '005', '250').",
    )
    dachser_consignor_id = fields.Char(
        string="Dachser Consignor Customer ID",
        help="8-digit customer number assigned by Dachser to your company.",
    )
    dachser_consignor_gln = fields.Char(
        string="Consignor GLN (Optional)",
        size=13,
        help="13-digit Global Location Number of your company if used in Dachser.",
    )

    # =========================================================================
    # OPERATIONAL SHIPMENT & PRODUCT PARAMETERS (OCA + ENHANCED)
    # =========================================================================
    dachser_operation_mode = fields.Selection(
        selection=DACHSER_OPERATION_MODES,
        string="Operation Mode",
        default="transportorder",
        help=(
            "- Full Transport Order (/rest/v2/transportorders): Creates the "
            "shipment in eLogistics/TMS and returns labels and SSCCs.\n"
            "- SSCC Labels + LDR Routing Only (/rest/v2/labels): Generates "
            "PDF/ZPL labels, SSCC license plates, and LDR routing code without "
            "recording a TMS order (compatible with immediate 10-day "
            "self-service test tokens)."
        ),
    )
    dachser_test_fallback_label_only = fields.Boolean(
        string="Fallback to /labels in Test Mode",
        default=True,
        help=(
            "If enabled in Test Environment and the 10-day self-service token "
            "is not yet activated for /transportorders, automatically falls "
            "back to /rest/v2/labels to generate real labels and SSCCs."
        ),
    )
    dachser_basket = fields.Selection(
        selection=DACHSER_BASKETS,
        string="eLogistics Basket",
        default="labelled",
        help=(
            "- imported: Creates an editable draft in eLogistics without label.\n"
            "- labelled: Creates the order in eLogistics and returns PDF/ZPL "
            "labels and SSCC codes (recommended).\n"
            "- sent: Creates the order, returns labels, and transmits it "
            "directly to Dachser TMS (not editable or cancellable via API)."
        ),
    )
    dachser_division = fields.Selection(
        selection=DACHSER_DIVISIONS,
        default="T",
        help="T = European Logistics (Industrial), F = Food Logistics.",
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
    dachser_product = fields.Selection(
        selection=DACHSER_PRODUCTS,
        string="Dachser Product / Service",
        default="Y",
        help=(
            "Dachser product code according to division (Y=targoflex, "
            "Z=targospeed, V=targofix, E=targospeed 12, X=targospeed plus, "
            "N=classicline, etc.)."
        ),
    )
    dachser_product_custom = fields.Char(
        string="Custom Product Code",
        size=5,
        help="Specific product code agreed with your Dachser branch.",
    )
    dachser_term = fields.Selection(
        selection=DACHSER_TERMS,
        string="Delivery Term (Frankatur)",
        default="031",
        help=(
            "031 = Free domicile (Freight Prepaid), "
            "011 / 021 = Ex Works (Freight Collect), etc."
        ),
    )
    dachser_term_custom = fields.Char(
        string="Custom Delivery Term Code",
        size=5,
    )
    dachser_use_order_incoterm = fields.Boolean(
        string="Map from Sale Order / Picking Incoterm",
        default=True,
        help=(
            "If the sale order or picking has an Incoterm (EXW, FCA, CPT, "
            "DAP, DDP...), automatically maps it to the corresponding "
            "Dachser Delivery Term code."
        ),
    )
    dachser_order_group = fields.Char(
        string="Order Group",
        size=30,
        help="Optional order grouping key in eLogistics (max. 30 characters).",
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
        string="Default Packaging Type",
        domain=[("package_carrier_type", "=", "dachser")],
        help="Default weight, height, width and length for packages",
    )
    dachser_default_package_type_id = fields.Many2one(
        comodel_name="stock.package.type",
        string="Default Package / Pallet Type",
        domain="[('package_carrier_type', '=', 'dachser')]",
        help=(
            "Default package/pallet type when the picking or sale order "
            "has no detailed packages."
        ),
    )
    dachser_default_packaging_code = fields.Selection(
        selection=DACHSER_PACKAGING_CODES,
        string="Default Dachser Packaging Code",
        default="EU",
        help=(
            "Default Dachser packaging code (EU = Euro Pallet, "
            "EP = Half Pallet, KT = Cardboard Box, PA = Pallet)."
        ),
    )
    dachser_default_content = fields.Char(
        string="Default Goods Description",
        default="Confectionery/Food",
        size=20,
        help=(
            "General content description sent to Dachser "
            "(max. 20 characters per API specification)."
        ),
    )

    # =========================================================================
    # LABEL OPTIONS (PDF / ZPL / EAN / DMC)
    # =========================================================================
    dachser_label_format = fields.Selection(
        selection=DACHSER_LABEL_FORMATS,
        default="P",
        help="P = Ready-to-print PDF; Z = ZPL for Zebra thermal printers.",
    )
    dachser_label_types = fields.Selection(
        selection=DACHSER_LABEL_TYPES,
        string="Label Barcode Types",
        default="EAN",
        help=(
            "EAN = Standard GS1-128 barcode; DMC = 2D DataMatrix; "
            "EAN,DMC = Both merged."
        ),
    )
    dachser_font_file_name = fields.Char(
        string="ZPL Font File Name",
        default="ARIALR.FNT",
        help=(
            "Font file installed on the Zebra printer (default ARIALR.FNT). "
            "Only applicable to ZPL format."
        ),
    )

    # =========================================================================
    # TRANSPORT & DELIVERY OPTIONS
    # =========================================================================
    dachser_collection_option = fields.Selection(
        selection=DACHSER_COLLECTION_OPTIONS,
        string="Collection Option",
        default="CN",
    )
    dachser_collection_time_from = fields.Char(
        string="Collection Time From (HH:MM)",
        default="09:00",
    )
    dachser_collection_time_to = fields.Char(
        string="Collection Time To (HH:MM)",
        default="18:00",
    )
    dachser_delivery_notice_type = fields.Selection(
        selection=DACHSER_DELIVERY_NOTICE_TYPES,
        string="Default Delivery Notice",
        default="none",
        help=(
            "Default delivery pre-notice if the consignee partner "
            "has none configured."
        ),
    )
    dachser_delivery_tail_lift = fields.Boolean(
        string="Default Tail-Lift Delivery",
        default=False,
    )
    dachser_self_collector = fields.Boolean(
        string="Consignee Self-Collector at Branch",
        default=False,
    )
    dachser_frost_protected = fields.Boolean(
        string="Frost Protected / Temperature Controlled",
        default=False,
    )

    # =========================================================================
    # TRANSPORT TARIFF & COST CALCULATION (QUOTATION API + LOCAL TARIFF TABLE)
    # =========================================================================
    dachser_rate_mode = fields.Selection(
        selection=DACHSER_RATE_MODES,
        string="Tariff Calculation Mode",
        default="api_with_fallback",
        help=(
            "- API Quotation with Local Tariff Table Fallback: Queries "
            "Dachser's /rest/v2/quotations endpoint in real time and, "
            "if no online rate is available for that destination or token, "
            "computes the rate using the local zone/weight/pallet tariff table.\n"
            "- Online API Quotation Only: Retrieves the quotation exclusively "
            "from Dachser's server.\n"
            "- Local Tariff Table Only: Computes immediately using the rules "
            "configured in Odoo without network requests."
        ),
    )
    dachser_logistics_type = fields.Selection(
        selection=DACHSER_LOGISTICS_TYPES,
        string="Quotation Logistics Type",
        default="D",
    )
    dachser_save_quotation = fields.Boolean(
        string="Save Quotation in eLogistics",
        default=False,
        help=(
            "If checked, rate inquiries (/rest/v2/quotations) are persisted "
            "in Dachser's eLogistics portal."
        ),
    )
    dachser_volumetric_factor = fields.Float(
        string="Volumetric Factor (kg / m³)",
        default=333.0,
        help=(
            "Volume-to-chargeable-weight conversion factor for road freight "
            "(Dachser standard: 1 m³ = 333 kg). Set 0 to use gross weight only."
        ),
    )
    dachser_ldm_factor = fields.Float(
        string="Loading Metre Factor (kg / LDM)",
        default=1850.0,
        help=(
            "Loading metre (LDM) to chargeable weight conversion factor "
            "(standard: 1 LDM = 1850 kg; 1 Euro Pallet = 0.4 LDM)."
        ),
    )
    dachser_fuel_surcharge_pct = fields.Float(
        string="Default Fuel Surcharge (%)",
        default=0.0,
        help=(
            "Default fuel surcharge percentage (BAF/Diesel) applied in the "
            "local tariff table when a rule does not specify its own."
        ),
    )
    dachser_tail_lift_surcharge = fields.Float(
        string="Default Tail-Lift Surcharge (€)",
        default=0.0,
        help=(
            "Default fixed surcharge when the shipment requires a tail-lift "
            "and the local rule does not define another amount."
        ),
    )
    dachser_notice_surcharge = fields.Float(
        string="Default Delivery Notice Surcharge (€)",
        default=0.0,
        help=(
            "Default fixed surcharge when the shipment includes "
            "phone/electronic pre-notice and the local rule does not define "
            "another amount."
        ),
    )
    dachser_free_for_customer = fields.Boolean(
        string="Free Shipping for Customer (Keep Internal Cost)",
        default=False,
        help=(
            "If enabled, the customer is charged 0.00 € on the sale order "
            "line, while Odoo still computes and stores the real Dachser cost "
            "on the sale order and picking for profitability analysis and "
            "carrier invoice auditing."
        ),
    )
    dachser_tariff_rule_ids = fields.One2many(
        comodel_name="dachser.tariff.rule",
        inverse_name="carrier_id",
        string="Tariff Table by Zones / Weights / Pallets",
        copy=True,
    )

    # =========================================================================
    # FIELD SYNCHRONIZATION BETWEEN OCA & ENHANCED FIELDS
    # =========================================================================
    @api.onchange("dachser_default_packaging_id")
    def _onchange_dachser_default_packaging_id(self):
        if self.dachser_default_packaging_id:
            self.dachser_default_package_type_id = self.dachser_default_packaging_id

    @api.onchange("dachser_default_package_type_id")
    def _onchange_dachser_default_package_type_id(self):
        if self.dachser_default_package_type_id:
            self.dachser_default_packaging_id = self.dachser_default_package_type_id

    @api.onchange("dachser_division", "dachser_product_t", "dachser_product_f")
    def _onchange_dachser_division_product(self):
        if self.dachser_division == "F" and self.dachser_product_f:
            self.dachser_product = self.dachser_product_f
        elif self.dachser_division == "T" and self.dachser_product_t:
            self.dachser_product = self.dachser_product_t

    @api.onchange("dachser_division", "dachser_packaging_t", "dachser_packaging_f")
    def _onchange_dachser_division_packaging(self):
        if self.dachser_division == "F" and self.dachser_packaging_f:
            self.dachser_default_packaging_code = self.dachser_packaging_f
        elif self.dachser_division == "T" and self.dachser_packaging_t:
            self.dachser_default_packaging_code = self.dachser_packaging_t

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("dachser_default_packaging_id") and not vals.get(
                "dachser_default_package_type_id"
            ):
                vals["dachser_default_package_type_id"] = vals[
                    "dachser_default_packaging_id"
                ]
            elif vals.get("dachser_default_package_type_id") and not vals.get(
                "dachser_default_packaging_id"
            ):
                vals["dachser_default_packaging_id"] = vals[
                    "dachser_default_package_type_id"
                ]
            if (
                vals.get("dachser_product")
                and "dachser_product_t" not in vals
                and vals.get("dachser_division", "T") == "T"
            ):
                if vals["dachser_product"] in dict(DACHSER_PRODUCTS_T):
                    vals["dachser_product_t"] = vals["dachser_product"]
            if (
                vals.get("dachser_default_packaging_code")
                and "dachser_packaging_t" not in vals
            ):
                if vals["dachser_default_packaging_code"] in dict(DACHSER_PACKAGING_T):
                    vals["dachser_packaging_t"] = vals["dachser_default_packaging_code"]
        return super().create(vals_list)

    def write(self, vals):
        if (
            "dachser_default_packaging_id" in vals
            and "dachser_default_package_type_id" not in vals
        ):
            vals = dict(
                vals,
                dachser_default_package_type_id=vals["dachser_default_packaging_id"],
            )
        elif (
            "dachser_default_package_type_id" in vals
            and "dachser_default_packaging_id" not in vals
        ):
            vals = dict(
                vals,
                dachser_default_packaging_id=vals["dachser_default_package_type_id"],
            )
        return super().write(vals)

    # =========================================================================
    # INTERNAL CONFIGURATION & CONVERSION HELPERS
    # =========================================================================
    def _dachser_get_client(self):
        self.ensure_one()
        return DachserRequest(self)

    def _dachser_get_product_code(self):
        self.ensure_one()
        if (
            self.dachser_product == "custom"
            or (self.dachser_division == "T" and self.dachser_product_t == "custom")
            or (self.dachser_division == "F" and self.dachser_product_f == "custom")
        ):
            return (self.dachser_product_custom or "Y").strip()
        if self.dachser_product and self.dachser_product != "Y":
            return self.dachser_product
        if self.dachser_division == "F" and self.dachser_product_f:
            return self.dachser_product_f
        if self.dachser_division == "T" and self.dachser_product_t:
            return self.dachser_product_t
        return self.dachser_product or "Y"

    def _dachser_get_term_code(self, order=None, picking=None):
        self.ensure_one()
        if self.dachser_use_order_incoterm:
            incoterm = False
            if picking and getattr(picking, "incoterm", False):
                incoterm = picking.incoterm
            elif (
                picking
                and picking.sale_id
                and getattr(picking.sale_id, "incoterm", False)
            ):
                incoterm = picking.sale_id.incoterm
            elif order and getattr(order, "incoterm", False):
                incoterm = order.incoterm
            if incoterm and incoterm.code in DACHSER_INCOTERM_TO_TERM:
                return DACHSER_INCOTERM_TO_TERM[incoterm.code]
        if self.dachser_term == "custom":
            return (self.dachser_term_custom or "031").strip()
        return self.dachser_term or "031"

    def _dachser_get_label_types_list(self):
        self.ensure_one()
        raw = self.dachser_label_types or "EAN"
        return [item.strip() for item in raw.split(",") if item.strip()]

    @staticmethod
    def _dachser_split_text(text, max_len=30, max_items=3):
        """Split a text string into up to `max_items` chunks of `max_len` chars."""
        cleaned = " ".join((text or "").strip().split())
        if not cleaned:
            return []
        chunks = []
        remaining = cleaned
        while remaining and len(chunks) < max_items:
            if len(remaining) <= max_len:
                chunks.append(remaining)
                break
            cut = remaining.rfind(" ", 0, max_len + 1)
            if cut <= 0:
                cut = max_len
            chunks.append(remaining[:cut].strip())
            remaining = remaining[cut:].strip()
        return chunks

    def _dachser_convert_weight_to_kg(self, weight):
        """Convert a weight value from Odoo's default weight UoM to kilograms (KG)."""
        if not weight:
            return 0.0
        weight_uom = self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter()
        kg_uom = self.env.ref("uom.product_uom_kgm", raise_if_not_found=False)
        if weight_uom and kg_uom and weight_uom != kg_uom:
            return weight_uom._compute_quantity(weight, kg_uom, round=False)
        return float(weight)

    def _dachser_convert_dimension_to_cm(self, dimension_value):
        """Convert a package dimension from Odoo's default length UoM
        (e.g. mm or m/cm) to integer centimetres.
        """
        if not dimension_value:
            return 0
        length_uom = self.env[
            "product.template"
        ]._get_length_uom_id_from_ir_config_parameter()
        cm_uom = self.env.ref("uom.product_uom_cm", raise_if_not_found=False)
        if length_uom and cm_uom and length_uom != cm_uom:
            cm_val = length_uom._compute_quantity(dimension_value, cm_uom, round=False)
        else:
            cm_val = float(dimension_value)
        return max(1, int(round(cm_val)))

    def _dachser_compute_chargeable_weight(
        self, gross_weight_kg, volume_m3=0.0, ldm=0.0
    ):
        """Compute chargeable weight comparing gross, volumetric (m³), and LDM."""
        self.ensure_one()
        vol_weight = (volume_m3 or 0.0) * (self.dachser_volumetric_factor or 0.0)
        ldm_weight = (ldm or 0.0) * (self.dachser_ldm_factor or 0.0)
        return max(float(gross_weight_kg or 0.0), vol_weight, ldm_weight)

    def _dachser_build_partner_payload(
        self, partner, include_id=False, is_consignor=False, minimal=False
    ):
        """Build `consignor` or `consignee` JSON block within Dachser API v2 limits."""
        self.ensure_one()
        if is_consignor and include_id and self.dachser_consignor_id and minimal:
            payload = {"id": self.dachser_consignor_id.strip()}
            if self.dachser_consignor_gln:
                payload["gln"] = self.dachser_consignor_gln.strip()
            return payload

        commercial_name = (
            partner.commercial_partner_id.name or partner.name or "Customer"
        )
        names = self._dachser_split_text(commercial_name, max_len=30, max_items=2)
        if partner.name and partner.name != commercial_name and len(names) < 3:
            names.extend(
                self._dachser_split_text(
                    partner.name, max_len=30, max_items=3 - len(names)
                )
            )
        if not names:
            names = ["Customer"]

        full_street = (
            " ".join(filter(None, [partner.street, partner.street2])).strip()
            or "No street"
        )
        street_chunks = self._dachser_split_text(full_street, max_len=30, max_items=3)
        primary_street = street_chunks[0] if street_chunks else "No street"
        supplement_parts = street_chunks[1:] if len(street_chunks) > 1 else []
        if partner.phone or partner.mobile:
            supplement_parts.append(f"Tel: {(partner.mobile or partner.phone).strip()}")

        country_code = (
            partner.country_id.code or self.env.company.country_id.code or "ES"
        ).upper()
        postal_code = (partner.zip or "00000").strip()[:10]
        city = (partner.city or partner.state_id.name or "City").strip()[:30]
        lang_iso = (partner.lang or self.env.user.lang or "es_ES")[:2].lower()

        address_info = {
            "streets": [primary_street],
            "city": city,
            "postalCode": postal_code,
            "countryCode": country_code,
        }
        if supplement_parts:
            address_info["supplementInformation"] = " - ".join(supplement_parts)[:60]

        payload = {
            "language": lang_iso,
            "names": names[:3],
            "addressInformation": address_info,
        }
        if is_consignor:
            if include_id and self.dachser_consignor_id:
                payload["id"] = self.dachser_consignor_id.strip()
            if self.dachser_consignor_gln:
                payload["partnerGLN"] = self.dachser_consignor_gln.strip()
        else:
            if include_id and partner.dachser_partner_id:
                payload["id"] = partner.dachser_partner_id.strip()
            if partner.dachser_gln:
                payload["partnerGLN"] = partner.dachser_gln.strip()
        return payload

    def _dachser_get_default_packaging_code(self):
        self.ensure_one()
        if (
            self.dachser_default_packaging_code
            and self.dachser_default_packaging_code != "EU"
        ):
            return self.dachser_default_packaging_code
        if self.dachser_division == "F" and self.dachser_packaging_f:
            return self.dachser_packaging_f
        if self.dachser_division == "T" and self.dachser_packaging_t:
            return self.dachser_packaging_t
        return self.dachser_default_packaging_code or "EU"

    def _dachser_get_package_dimensions_cm(self, package_type=None):
        """Return (length_cm, width_cm, height_cm, packaging_code, unit_ldm)
        from a `stock.package.type`.
        """
        self.ensure_one()
        pkg_type = (
            package_type
            or self.dachser_default_package_type_id
            or self.dachser_default_packaging_id
        )
        shipper_code = (
            pkg_type.shipper_package_code
            if pkg_type
            and pkg_type.shipper_package_code
            and pkg_type.shipper_package_code != "default"
            else None
        )
        pkg_code = (
            (
                pkg_type.dachser_packaging_code
                if pkg_type and pkg_type.dachser_packaging_code
                else None
            )
            or shipper_code
            or self._dachser_get_default_packaging_code()
            or "EU"
        )
        if (
            pkg_type
            and pkg_type.packaging_length
            and pkg_type.width
            and pkg_type.height
        ):
            l_cm = self._dachser_convert_dimension_to_cm(pkg_type.packaging_length)
            w_cm = self._dachser_convert_dimension_to_cm(pkg_type.width)
            h_cm = self._dachser_convert_dimension_to_cm(pkg_type.height)
        elif pkg_code == "EU":
            l_cm, w_cm, h_cm = 120, 80, 120
        elif pkg_code in ("EP", "DD", "HE", "HP"):
            l_cm, w_cm, h_cm = 80, 60, 100
        elif pkg_code == "IP":
            l_cm, w_cm, h_cm = 120, 100, 120
        else:
            l_cm, w_cm, h_cm = 60, 40, 40

        if pkg_code == "EU":
            unit_ldm = 0.4
        elif pkg_code in ("EP", "DD", "HE", "HP"):
            unit_ldm = 0.2
        elif pkg_code == "IP":
            unit_ldm = 0.5
        else:
            unit_ldm = round((l_cm / 100.0) * (w_cm / 100.0) / 2.4, 2)
        return l_cm, w_cm, h_cm, pkg_code, unit_ldm

    def _dachser_estimate_order_weight_and_packages(self, order):
        """Compute (gross_weight_kg, volume_m3, ldm, packages_qty, order_lines)
        from a `sale.order`, supporting standard and packaging weights.
        """
        self.ensure_one()
        total_weight_kg = 0.0
        for line in order.order_line.filtered(
            lambda ol: not ol.is_delivery
            and not ol.display_type
            and ol.product_id.type in ("consu", "product")
        ):
            line_weight = 0.0
            if line.product_id.weight:
                line_weight = line.product_id.weight * line.product_uom_qty
            elif hasattr(line.product_id, "_get_packaging_unit_weight"):
                pkg_unit_weight = line.product_id._get_packaging_unit_weight(
                    packaging=line.product_packaging_id,
                    weight_type="gross",
                )
                line_weight = (pkg_unit_weight or 0.0) * line.product_uom_qty
            total_weight_kg += self._dachser_convert_weight_to_kg(line_weight)

        if total_weight_kg <= 0.0:
            fallback_weight = (
                order._get_estimated_weight()
                if hasattr(order, "_get_estimated_weight")
                else 0.0
            )
            total_weight_kg = max(
                1.0, self._dachser_convert_weight_to_kg(fallback_weight) or 1.0
            )

        l_cm, w_cm, h_cm, pkg_code, unit_ldm = self._dachser_get_package_dimensions_cm()
        default_pkg = (
            self.dachser_default_package_type_id or self.dachser_default_packaging_id
        )
        max_pkg_weight = (
            self._dachser_convert_weight_to_kg(default_pkg.max_weight)
            if default_pkg and default_pkg.max_weight > 0
            else (
                700.0
                if pkg_code in ("EU", "PA", "IP", "EP", "DD", "HE", "HP")
                else 25.0
            )
        )
        packages_qty = (
            max(1, int(math.ceil(total_weight_kg / max_pkg_weight)))
            if max_pkg_weight > 0
            else 1
        )
        unit_vol_m3 = (l_cm / 100.0) * (w_cm / 100.0) * (h_cm / 100.0)
        total_vol_m3 = round(unit_vol_m3 * packages_qty, 3)
        total_ldm = round(unit_ldm * packages_qty, 2)
        content_str = (self.dachser_default_content or "Goods")[:20]

        order_lines = [
            {
                "quantity": packages_qty,
                "packaging": pkg_code,
                "content": content_str,
                "weight": {
                    "weight": round(total_weight_kg, 2),
                    "unit": "KG",
                },
                "loadingMetre": total_ldm,
                "measure": {
                    "length": l_cm,
                    "width": w_cm,
                    "height": h_cm,
                    "unit": "CM",
                    "volume": {
                        "amount": max(0.01, round(total_vol_m3, 2)),
                        "unit": "M3",
                    },
                },
            }
        ]
        return total_weight_kg, total_vol_m3, total_ldm, packages_qty, order_lines

    def _dachser_prepare_picking_lines(self, picking):
        """Build `transportOrderLines` and totals from physical packages,
        OCA `number_of_packages`, and OCA `picking.volume`.
        """
        self.ensure_one()
        move_desc = (
            picking.move_ids_without_package[:1].description_picking
            if picking.move_ids_without_package
            else False
        )
        content_str = (
            picking.dachser_content_override
            or self.dachser_default_content
            or move_desc
            or "Goods"
        )[:20]
        packages = picking.move_line_ids.mapped("result_package_id")

        order_lines = []
        total_weight_kg = 0.0
        total_vol_m3 = 0.0
        total_ldm = 0.0
        total_packages_qty = 0

        if packages:
            for pkg in packages:
                pkg_type = (
                    pkg.package_type_id
                    or self.dachser_default_package_type_id
                    or self.dachser_default_packaging_id
                )
                l_cm, w_cm, h_cm, pkg_code, unit_ldm = (
                    self._dachser_get_package_dimensions_cm(pkg_type)
                )
                pkg_weight = getattr(pkg, "shipping_weight", 0.0) or getattr(
                    pkg, "weight", 0.0
                )
                pkg_weight_kg = self._dachser_convert_weight_to_kg(pkg_weight)
                if pkg_weight_kg <= 0.0:
                    pkg_moves_weight = sum(
                        ml.product_id.weight * ml.quantity
                        for ml in picking.move_line_ids
                        if ml.result_package_id == pkg
                    )
                    pkg_weight_kg = max(
                        1.0, self._dachser_convert_weight_to_kg(pkg_moves_weight)
                    )

                vol_m3 = max(
                    0.01, round((l_cm / 100.0) * (w_cm / 100.0) * (h_cm / 100.0), 2)
                )
                total_weight_kg += pkg_weight_kg
                total_vol_m3 += vol_m3
                total_ldm += unit_ldm
                total_packages_qty += 1

                order_lines.append(
                    {
                        "quantity": 1,
                        "packaging": pkg_code,
                        "content": content_str,
                        "weight": {
                            "weight": str(round(pkg_weight_kg, 2)),
                            "unit": "KG",
                        },
                        "loadingMetre": round(unit_ldm, 2),
                        "measure": {
                            "length": l_cm,
                            "width": w_cm,
                            "height": h_cm,
                            "unit": "CM",
                            "volume": {
                                "amount": str(vol_m3),
                                "unit": "M3",
                            },
                        },
                    }
                )
        else:
            raw_weight = picking.shipping_weight or picking.weight or 0.0
            total_weight_kg = self._dachser_convert_weight_to_kg(raw_weight)
            if total_weight_kg <= 0.0:
                for move in picking.move_ids.filtered(lambda m: m.state != "cancel"):
                    if move.product_id.weight:
                        total_weight_kg += self._dachser_convert_weight_to_kg(
                            move.product_id.weight
                            * (move.quantity or move.product_uom_qty)
                        )
                    elif hasattr(move.product_id, "_get_packaging_unit_weight"):
                        w_unit = move.product_id._get_packaging_unit_weight(
                            packaging=move.product_packaging_id,
                            weight_type="gross",
                        )
                        total_weight_kg += self._dachser_convert_weight_to_kg(
                            (w_unit or 0.0) * (move.quantity or move.product_uom_qty)
                        )
            total_weight_kg = max(1.0, total_weight_kg)

            l_cm, w_cm, h_cm, pkg_code, unit_ldm = (
                self._dachser_get_package_dimensions_cm(
                    picking.dachser_package_type_id
                    or self.dachser_default_package_type_id
                    or self.dachser_default_packaging_id
                )
            )
            # Use OCA `number_of_packages` or `dachser_packages_qty`
            total_packages_qty = max(
                1,
                getattr(picking, "number_of_packages", 0)
                or picking.dachser_packages_qty
                or 1,
            )
            # Use OCA `picking.volume` if > 0, else compute from package dimensions
            picking_vol = getattr(picking, "volume", 0.0) or 0.0
            unit_vol_m3 = (l_cm / 100.0) * (w_cm / 100.0) * (h_cm / 100.0)
            total_vol_m3 = (
                round(picking_vol, 3)
                if picking_vol > 0.0
                else max(0.01, round(unit_vol_m3 * total_packages_qty, 2))
            )
            total_ldm = round(unit_ldm * total_packages_qty, 2)

            order_lines.append(
                {
                    "quantity": total_packages_qty,
                    "packaging": pkg_code,
                    "content": content_str,
                    "weight": {
                        "weight": str(round(total_weight_kg, 2)),
                        "unit": "KG",
                    },
                    "loadingMetre": total_ldm,
                    "measure": {
                        "length": l_cm,
                        "width": w_cm,
                        "height": h_cm,
                        "unit": "CM",
                        "volume": {
                            "amount": str(max(0.01, round(total_vol_m3, 2))),
                            "unit": "M3",
                        },
                    },
                }
            )

        return total_weight_kg, total_vol_m3, total_ldm, total_packages_qty, order_lines

    def _dachser_build_transport_options(self, partner, picking=None):
        """Build `transportOptions` for transport orders and quotations."""
        self.ensure_one()
        tail_lift = (
            picking.dachser_tail_lift
            if picking and picking.dachser_tail_lift
            else (partner.dachser_tail_lift or self.dachser_delivery_tail_lift)
        )
        notice_type = (
            picking.dachser_delivery_notice_type
            if picking
            and picking.dachser_delivery_notice_type
            and picking.dachser_delivery_notice_type != "none"
            else (
                partner.dachser_delivery_notice_type
                if partner.dachser_delivery_notice_type
                and partner.dachser_delivery_notice_type != "none"
                else self.dachser_delivery_notice_type
            )
        )

        options = {
            "collectionOption": self.dachser_collection_option or "CN",
            "deliveryTailLift": bool(tail_lift),
            "selfCollector": bool(self.dachser_self_collector),
            "frostProtected": bool(self.dachser_frost_protected),
        }
        if self.dachser_collection_time_from:
            options["collectionTimeFrom"] = self.dachser_collection_time_from.strip()
        if self.dachser_collection_time_to:
            options["collectionTimeTo"] = self.dachser_collection_time_to.strip()
        if picking and picking.dachser_fixed_delivery_date:
            options["fixedDate"] = fields.Date.to_string(
                picking.dachser_fixed_delivery_date
            )

        if notice_type and notice_type in ("AS", "AI", "TE", "SM", "EM", "AV"):
            notice_entry = {
                "type": notice_type if notice_type in ("AS", "AI") else "AS",
                "name": (
                    partner.name or partner.commercial_partner_id.name or "Contact"
                )[:30],
            }
            if partner.mobile:
                notice_entry["mobilePhone"] = partner.mobile.strip()[:25]
            if partner.phone:
                notice_entry["phone"] = partner.phone.strip()[:25]
            elif partner.mobile:
                notice_entry["phone"] = partner.mobile.strip()[:25]
            if partner.email:
                notice_entry["mail"] = partner.email.strip()[:60]
            options["deliveryNoticeOptions"] = [notice_entry]

        return options, bool(tail_lift), (notice_type or "none")

    # =========================================================================
    # TRANSPORT TARIFF CALCULATION (QUOTATION API + LOCAL TARIFF TABLE)
    # =========================================================================
    def _dachser_rate_from_tariff_table(
        self,
        partner,
        chargeable_weight_kg,
        packages_qty=1,
        tail_lift=False,
        notice_type="none",
    ):
        """Evaluate `dachser.tariff.rule` records and return (cost, breakdown, rule)."""
        self.ensure_one()
        active_rules = self.dachser_tariff_rule_ids.filtered("active").sorted(
            "sequence"
        )
        for rule in active_rules:
            if rule._match_destination_and_shipment(
                partner, chargeable_weight_kg, packages_qty
            ):
                cost, breakdown = rule._compute_rule_cost(
                    chargeable_weight_kg=chargeable_weight_kg,
                    packages_qty=packages_qty,
                    tail_lift=tail_lift,
                    has_notice=(notice_type != "none"),
                )
                return cost, breakdown, rule
        return None, None, None

    def _dachser_rate_from_quotation_api(
        self,
        partner,
        order_lines,
        term_code,
        transport_options,
        reference_value=None,
    ):
        """Query `POST /rest/v2/quotations` and return
        (cost, currency, quotation_id, breakdown).
        """
        self.ensure_one()
        client = self._dachser_get_client()
        quotation_lines = []
        for line in order_lines:
            q_line = dict(line)
            q_line["weight"] = {
                "weight": float(line["weight"]["weight"]),
                "unit": "KG",
            }
            if "measure" in line and "volume" in line["measure"]:
                q_measure = dict(line["measure"])
                q_measure["volume"] = {
                    "amount": float(line["measure"]["volume"]["amount"]),
                    "unit": "M3",
                }
                q_line["measure"] = q_measure
            quotation_lines.append(q_line)

        transport_order = {
            "transportDate": fields.Date.to_string(fields.Date.context_today(self)),
            "division": self.dachser_division or "T",
            "product": self._dachser_get_product_code(),
            "term": term_code,
            "consignor": {"id": (self.dachser_consignor_id or "00000000").strip()},
            "consignee": self._dachser_build_partner_payload(
                partner, include_id=False, is_consignor=False
            ),
            "transportOptions": transport_options,
            "transportOrderLines": quotation_lines,
        }
        if reference_value:
            transport_order["references"] = [
                {"code": "100", "value": str(reference_value)[:35]}
            ]

        payload = {
            "logisticsType": self.dachser_logistics_type or "D",
            "saveQuotation": bool(self.dachser_save_quotation),
            "transportOrder": transport_order,
        }

        res = client.get_quotation(payload)
        total_block = res.get("totalAmount") or {}
        amount = float(total_block.get("amount") or 0.0)
        currency_code = total_block.get("currency") or "EUR"
        quotation_id = res.get("id") or ""

        details_lines = []
        for detail in res.get("quotationDetails") or []:
            stype = detail.get("serviceType") or ""
            sdesc = detail.get("serviceTypeDescription") or stype
            samount_block = detail.get("serviceTypeAmount") or {}
            samount = float(samount_block.get("amount") or 0.0)
            scurr = samount_block.get("currency") or currency_code
            details_lines.append(f"• [{stype}] {sdesc}: {samount:.2f} {scurr}")

        if res.get("remarks"):
            details_lines.append(_("Remarks: %s") % "; ".join(res["remarks"]))

        header_line = _("Dachser API Quotation #%(qid)s: %(amt).2f %(curr)s") % {
            "qid": quotation_id or "N/A",
            "amt": amount,
            "curr": currency_code,
        }
        breakdown = header_line + (
            "\n" + "\n".join(details_lines) if details_lines else ""
        )
        return amount, currency_code, quotation_id, breakdown

    def dachser_rate_shipment(self, order):
        """Calculate shipping rate for a `sale.order` (Quotation API + Local
        Tariff Table + Volumetric Weight) and store the internal estimated cost
        and breakdown on the sale order even if shipping is free.
        """
        self.ensure_one()
        partner = order.partner_shipping_id or order.partner_id
        if not partner.country_id or not partner.zip:
            return {
                "success": False,
                "price": 0.0,
                "error_message": _(
                    "The consignee (%s) must have a Postal Code and Country "
                    "to calculate the Dachser rate."
                )
                % partner.display_name,
                "warning_message": False,
            }

        gross_weight_kg, total_vol_m3, total_ldm, packages_qty, order_lines = (
            self._dachser_estimate_order_weight_and_packages(order)
        )
        chargeable_weight_kg = self._dachser_compute_chargeable_weight(
            gross_weight_kg=gross_weight_kg,
            volume_m3=total_vol_m3,
            ldm=total_ldm,
        )
        term_code = self._dachser_get_term_code(order=order)
        transport_options, tail_lift, notice_type = (
            self._dachser_build_transport_options(partner)
        )

        cost = None
        currency_code = "EUR"
        quotation_id = False
        breakdown = ""
        warning_message = False

        summary_line = _(
            "Gross weight: %(gross).2f kg | Vol: %(vol).3f m³ | "
            "Chargeable weight: %(chg).2f kg | Packages: %(pkgs)d"
        ) % {
            "gross": gross_weight_kg,
            "vol": total_vol_m3,
            "chg": chargeable_weight_kg,
            "pkgs": packages_qty,
        }

        # 1. Try Quotation API if applicable
        if self.dachser_rate_mode in ("api_quotation", "api_with_fallback"):
            try:
                api_cost, api_curr, q_id, api_breakdown = (
                    self._dachser_rate_from_quotation_api(
                        partner=partner,
                        order_lines=order_lines,
                        term_code=term_code,
                        transport_options=transport_options,
                        reference_value=order.name,
                    )
                )
                if api_cost > 0:
                    cost = api_cost
                    currency_code = api_curr
                    quotation_id = q_id
                    breakdown = f"{api_breakdown}\n{summary_line}"
                elif self.dachser_rate_mode == "api_quotation":
                    return {
                        "success": False,
                        "price": 0.0,
                        "error_message": _(
                            "Dachser Quotation API did not return an immediate "
                            "price for this shipment (HTTP 202 / no automatic price)."
                        ),
                        "warning_message": False,
                    }
            except UserError as exc:
                if self.dachser_rate_mode == "api_quotation":
                    return {
                        "success": False,
                        "price": 0.0,
                        "error_message": str(exc),
                        "warning_message": False,
                    }
                warning_message = _(
                    "Notice: Could not retrieve online quotation from Dachser "
                    "API (%s). Local tariff table has been applied."
                ) % str(exc)

        # 2. Use Local Tariff Table if in tariff_table mode or as fallback
        if cost is None:
            table_cost, table_breakdown, matched_rule = (
                self._dachser_rate_from_tariff_table(
                    partner=partner,
                    chargeable_weight_kg=chargeable_weight_kg,
                    packages_qty=packages_qty,
                    tail_lift=tail_lift,
                    notice_type=notice_type,
                )
            )
            if table_cost is None:
                return {
                    "success": False,
                    "price": 0.0,
                    "error_message": _(
                        "No matching rule found in Dachser Tariff Table for "
                        "%(partner)s (ZIP %(zip)s, %(country)s, "
                        "%(weight).2f chargeable kg, %(pkgs)s packages)."
                    )
                    % {
                        "partner": partner.display_name,
                        "zip": partner.zip,
                        "country": partner.country_id.name,
                        "weight": chargeable_weight_kg,
                        "pkgs": packages_qty,
                    },
                    "warning_message": False,
                }
            cost = table_cost
            currency_code = (
                matched_rule.currency_id.name if matched_rule.currency_id else "EUR"
            )
            breakdown = f"{table_breakdown}\n{summary_line}"

        # 3. Convert currency to sale order currency if different
        order_currency = (
            order.currency_id
            or order.company_id.currency_id
            or self.env.company.currency_id
        )
        source_currency = (
            self.env["res.currency"].search([("name", "=", currency_code)], limit=1)
            or order_currency
        )
        if source_currency != order_currency:
            cost_in_order_curr = source_currency._convert(
                cost,
                order_currency,
                order.company_id or self.env.company,
                order.date_order or fields.Date.context_today(self),
            )
        else:
            cost_in_order_curr = cost

        # 4. Always store the internal estimated cost on the sale order
        order.sudo().write(
            {
                "dachser_estimated_cost": cost_in_order_curr,
                "dachser_quotation_id": quotation_id or False,
                "dachser_rate_breakdown": breakdown,
                "dachser_chargeable_weight": chargeable_weight_kg,
            }
        )

        # 5. If carrier is configured as free for customer, return 0.0 as sale price
        customer_price = (
            0.0 if self.dachser_free_for_customer else float(cost_in_order_curr)
        )

        return {
            "success": True,
            "price": customer_price,
            "error_message": False,
            "warning_message": warning_message,
        }

    # =========================================================================
    # PICKING SHIPMENT SUBMISSION, LABELS & TRACKING (STOCK.PICKING)
    # =========================================================================
    def _dachser_build_references(self, picking):
        """Build `references` list for Dachser (code 100 mandatory, max 35 chars)."""
        ref_100 = (picking.name or picking.origin or "SHIPMENT")[:35]
        refs = [{"code": "100", "value": ref_100}]
        if picking.sale_id and picking.sale_id.client_order_ref:
            refs.append({"code": "101", "value": picking.sale_id.client_order_ref[:35]})
        elif picking.origin and picking.origin != picking.name:
            refs.append({"code": "102", "value": picking.origin[:35]})
        return refs

    def _dachser_attach_label_to_picking(
        self, picking, label_b64, tracking_ref, is_return=False
    ):
        """Decode base64 PDF/ZPL label and attach it to the picking chatter."""
        self.ensure_one()
        if not label_b64:
            return False
        ext = "zpl" if self.dachser_label_format == "Z" else "pdf"
        mimetype = "text/plain" if ext == "zpl" else "application/pdf"
        prefix = "Dachser_Return" if is_return else "Dachser_Label"
        safe_ref = (str(tracking_ref or picking.name or "shipment")).replace("/", "_")
        filename = f"{prefix}_{safe_ref}.{ext}"
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
                    "name": filename,
                    "datas": base64.b64encode(raw_bytes),
                    "type": "binary",
                    "res_model": "stock.picking",
                    "res_id": picking.id,
                    "mimetype": mimetype,
                }
            )
        )

    @api.model
    def _dachser_validate_picking_partner(self, picking):
        partner = picking.partner_id
        if not partner:
            raise UserError(
                _("Picking %s does not have a delivery address assigned.")
                % picking.name
            )
        if not partner.country_id or not partner.zip or not partner.city:
            raise UserError(
                _(
                    "Consignee %s must have Street, City, Postal Code, "
                    "and Country configured."
                )
                % partner.display_name
            )
        return partner

    def _dachser_submit_picking_order(
        self,
        picking,
        client,
        shipper_partner,
        partner,
        order_lines,
        packages_qty,
        term_code,
        transport_options,
        references,
    ):
        ship_date = fields.Date.to_string(
            picking.scheduled_date.date()
            if picking.scheduled_date
            else fields.Date.context_today(self)
        )
        label_types = self._dachser_get_label_types_list()
        mode = self.dachser_operation_mode or "transportorder"
        result = {
            "order_id": False,
            "order_state": False,
            "ssccs": [],
            "label_b64": False,
            "ldr_routing": False,
            "api_messages": [],
        }

        if mode == "transportorder":
            to_payload = {
                "transportDate": ship_date,
                "labelFormat": self.dachser_label_format or "P",
                "labelTypes": label_types,
                "division": self.dachser_division or "T",
                "product": self._dachser_get_product_code(),
                "term": term_code,
                "forwarder": {"id": (self.dachser_forwarder_id or "193").strip()},
                "consignor": self._dachser_build_partner_payload(
                    shipper_partner,
                    include_id=True,
                    is_consignor=True,
                    minimal=bool(self.dachser_consignor_id),
                ),
                "consignee": self._dachser_build_partner_payload(
                    partner, include_id=True, is_consignor=False
                ),
                "references": references,
                "transportOrderLines": order_lines,
                "transportOptions": transport_options,
            }
            if self.dachser_label_format == "Z" and self.dachser_font_file_name:
                to_payload["fontFileName"] = self.dachser_font_file_name.strip()
            if self.dachser_order_group:
                to_payload["orderGroup"] = self.dachser_order_group.strip()[:30]
            if picking.dachser_driver_notes:
                to_payload["texts"] = [
                    {
                        "code": "ZU",
                        "value": picking.dachser_driver_notes.strip()[:70],
                    }
                ]

            try:
                to_resp = client.create_transport_order(
                    basket=self.dachser_basket or "labelled",
                    payload=to_payload,
                )
                result.update(
                    {
                        "order_id": str(to_resp.get("id") or ""),
                        "order_state": to_resp.get("state")
                        or (self.dachser_basket or "labelled"),
                        "ssccs": to_resp.get("ssccs") or [],
                        "label_b64": to_resp.get("label") or False,
                        "api_messages": to_resp.get("messages") or [],
                    }
                )
            except UserError as exc:
                if not self.prod_environment and self.dachser_test_fallback_label_only:
                    _logger.info(
                        "Dachser test fallback to /rest/v2/labels for %s (%s)",
                        picking.name,
                        exc,
                    )
                    mode = "label_only"
                else:
                    raise

        if mode == "label_only":
            label_payload = {
                "format": (self.dachser_label_format or "P").upper(),
                "count": min(10, max(1, packages_qty)),
                "fontFileName": (self.dachser_font_file_name or "ARIALR.FNT").strip(),
                "labelTypes": label_types,
                "shipment": {
                    "division": self.dachser_division or "T",
                    "product": self._dachser_get_product_code(),
                    "shipmentDate": ship_date,
                    "forwarder": {"id": (self.dachser_forwarder_id or "193").strip()},
                    "consignor": self._dachser_build_partner_payload(
                        shipper_partner,
                        include_id=True,
                        is_consignor=True,
                        minimal=False,
                    ),
                    "consignee": self._dachser_build_partner_payload(
                        partner,
                        include_id=False,
                        is_consignor=False,
                        minimal=False,
                    ),
                    "references": references,
                },
            }
            lbl_resp = client.generate_standalone_label(label_payload)
            relation_info = lbl_resp.get("relation") or {}
            result.update(
                {
                    "ssccs": lbl_resp.get("ssccs") or [],
                    "label_b64": lbl_resp.get("label") or False,
                    "ldr_routing": relation_info.get("printableRelation")
                    or relation_info.get("relationCode")
                    or False,
                    "order_state": "labelled",
                }
            )
        return result

    def _dachser_post_shipping_chatter(self, picking, attachment, chatter_data):
        tracking_url = self.dachser_get_tracking_link(
            picking, tracking_override=chatter_data["primary_tracking"]
        )
        msg_items = [
            Markup("<li><b>%s:</b> %s</li>")
            % (_("Dachser Order State"), chatter_data["order_state"] or "labelled"),
            Markup("<li><b>%s:</b> <a href='%s' target='_blank'>%s</a></li>")
            % (_("Tracking / SSCC"), tracking_url, chatter_data["all_tracking_refs"]),
            Markup("<li><b>%s:</b> %.2f kg / %.2f kg (%d)</li>")
            % (
                _("Gross / Chargeable Weight"),
                chatter_data["gross_weight_kg"],
                chatter_data["chargeable_weight_kg"],
                chatter_data["packages_qty"],
            ),
        ]
        if chatter_data["order_id"]:
            msg_items.insert(
                0,
                Markup("<li><b>%s:</b> %s</li>")
                % (_("Dachser Order ID"), chatter_data["order_id"]),
            )
        if chatter_data["ldr_routing"]:
            msg_items.append(
                Markup("<li><b>%s:</b> %s</li>")
                % (_("Dachser LDR Route"), chatter_data["ldr_routing"])
            )
        if chatter_data["estimated_cost"]:
            msg_items.append(
                Markup("<li><b>%s:</b> %.2f €</li>")
                % (_("Estimated Freight Cost"), chatter_data["estimated_cost"])
            )
        if chatter_data["api_messages"]:
            msg_items.append(
                Markup("<li><b>%s:</b> %s</li>")
                % (_("API Notices"), ", ".join(chatter_data["api_messages"]))
            )

        body = (
            Markup("<p><b>%s</b></p><ul>") % _("Shipment successfully sent to Dachser:")
            + Markup("").join(msg_items)
            + Markup("</ul>")
        )
        picking.message_post(
            body=body,
            attachment_ids=[attachment.id] if attachment else [],
        )

    def _dachser_compute_picking_estimated_cost(
        self,
        picking,
        partner,
        chargeable_weight_kg,
        packages_qty,
        tail_lift,
        notice_type,
    ):
        if picking.sale_id and picking.sale_id.dachser_estimated_cost:
            return (
                picking.sale_id.dachser_estimated_cost,
                picking.sale_id.dachser_rate_breakdown or "",
            )
        table_cost, table_breakdown, _rule = self._dachser_rate_from_tariff_table(
            partner=partner,
            chargeable_weight_kg=chargeable_weight_kg,
            packages_qty=packages_qty,
            tail_lift=tail_lift,
            notice_type=notice_type,
        )
        if table_cost is not None:
            return table_cost, table_breakdown
        return 0.0, ""

    @staticmethod
    def _dachser_write_sent_picking_vals(picking, vals):
        packages_qty = vals["dachser_packages_qty"]
        if "number_of_packages" in picking._fields and not picking.number_of_packages:
            vals["number_of_packages"] = packages_qty
        if "delivery_state" in picking._fields:
            vals["delivery_state"] = "shipping_recorded_in_carrier"
        if (
            "tracking_state_history" in picking._fields
            and not picking.tracking_state_history
        ):
            vals["tracking_state_history"] = vals.get("dachser_order_state") or "sent"
        picking.write(vals)

    def dachser_send_shipping(self, pickings):
        """Send pickings to Dachser (`POST /rest/v2/transportorders/{basket}`
        or `POST /rest/v2/labels`), attach PDF/ZPL labels, assign SSCC codes,
        and record tracking details (including OCA `delivery_state` fields).
        """
        res = []
        client = self._dachser_get_client()

        for picking in pickings:
            partner = self._dachser_validate_picking_partner(picking)
            shipper_partner = (
                picking.picking_type_id.warehouse_id.partner_id
                or picking.company_id.partner_id
                or self.env.company.partner_id
            )
            gross_weight_kg, total_vol_m3, total_ldm, packages_qty, order_lines = (
                self._dachser_prepare_picking_lines(picking)
            )
            chargeable_weight_kg = self._dachser_compute_chargeable_weight(
                gross_weight_kg=gross_weight_kg,
                volume_m3=total_vol_m3,
                ldm=total_ldm,
            )
            term_code = self._dachser_get_term_code(picking=picking)
            transport_options, tail_lift, notice_type = (
                self._dachser_build_transport_options(partner, picking=picking)
            )
            references = self._dachser_build_references(picking)

            ship_result = self._dachser_submit_picking_order(
                picking=picking,
                client=client,
                shipper_partner=shipper_partner,
                partner=partner,
                order_lines=order_lines,
                packages_qty=packages_qty,
                term_code=term_code,
                transport_options=transport_options,
                references=references,
            )
            order_id = ship_result["order_id"]
            order_state = ship_result["order_state"]
            ssccs = ship_result["ssccs"]
            label_b64 = ship_result["label_b64"]
            ldr_routing = ship_result["ldr_routing"]

            # Assign SSCC to each physical Odoo package if present
            packages = picking.move_line_ids.mapped("result_package_id")
            for idx, pkg in enumerate(packages):
                if idx < len(ssccs):
                    pkg.dachser_sscc = ssccs[idx]

            primary_tracking = ssccs[0] if ssccs else (order_id or picking.name)
            all_tracking_refs = ", ".join(ssccs) if ssccs else primary_tracking

            estimated_cost, cost_breakdown = (
                self._dachser_compute_picking_estimated_cost(
                    picking=picking,
                    partner=partner,
                    chargeable_weight_kg=chargeable_weight_kg,
                    packages_qty=packages_qty,
                    tail_lift=tail_lift,
                    notice_type=notice_type,
                )
            )

            self._dachser_write_sent_picking_vals(
                picking,
                {
                    "dachser_transport_order_id": order_id,
                    "dachser_order_state": order_state,
                    "dachser_shipment_state": "registered",
                    "dachser_sscc_refs": ", ".join(ssccs) if ssccs else False,
                    "dachser_ldr_routing": ldr_routing,
                    "dachser_estimated_cost": estimated_cost,
                    "dachser_chargeable_weight": chargeable_weight_kg,
                    "dachser_cost_breakdown": cost_breakdown,
                    "dachser_packages_qty": packages_qty,
                },
            )

            attachment = self._dachser_attach_label_to_picking(
                picking=picking,
                label_b64=label_b64,
                tracking_ref=primary_tracking,
                is_return=False,
            )
            self._dachser_post_shipping_chatter(
                picking,
                attachment,
                {
                    "order_id": order_id,
                    "order_state": order_state,
                    "primary_tracking": primary_tracking,
                    "all_tracking_refs": all_tracking_refs,
                    "gross_weight_kg": gross_weight_kg,
                    "chargeable_weight_kg": chargeable_weight_kg,
                    "packages_qty": packages_qty,
                    "ldr_routing": ldr_routing,
                    "estimated_cost": estimated_cost,
                    "api_messages": ship_result["api_messages"],
                },
            )

            res.append(
                {
                    "exact_price": estimated_cost,
                    "tracking_number": all_tracking_refs,
                }
            )
        return res

    def dachser_get_tracking_link(self, picking, tracking_override=None):
        """Return direct tracking link to Dachser eLogistics ShipmentPointer."""
        self.ensure_one()
        raw_ref = (
            tracking_override
            or picking.carrier_tracking_ref
            or picking.dachser_consignment_id
            or picking.name
        )
        first_ref = str(raw_ref).split(",")[0].strip() if raw_ref else picking.name
        lang_code = picking.partner_id.lang or self.env.user.lang or "es_ES"
        if "_" not in lang_code:
            lang_code = "es_ES"
        return DACHSER_TRACKING_URL_TEMPLATE.format(
            lang=lang_code, tracking_ref=first_ref
        )

    def dachser_cancel_shipment(self, pickings):
        """Cancel the transport order (`DELETE /rest/v2/transportorders/{id}`)
        as long as it has not yet been transmitted to the TMS (`state != 'sent'`).
        """
        client = self._dachser_get_client()
        for picking in pickings:
            order_ref = (
                picking.dachser_transport_order_id or picking.carrier_tracking_ref
            )
            if picking.dachser_order_state == "sent":
                raise UserError(
                    _(
                        "It is not possible to cancel a shipment because it has "
                        "already been sent (Dachser order #%s is in state 'sent')."
                    )
                    % (order_ref or picking.name)
                )
            if order_ref:
                resp = client.delete_transport_order(order_ref, raise_on_error=False)
                if isinstance(resp, dict) and resp.get("_error"):
                    raise UserError(
                        _(
                            "It is not possible to cancel a shipment because "
                            "it has already been sent.\n%s"
                        )
                        % resp.get("error_message", "")
                    )

            cancel_vals = {
                "carrier_tracking_ref": False,
                "dachser_transport_order_id": False,
                "dachser_order_state": "cancelled",
                "dachser_shipment_state": "cancelled",
                "dachser_sscc_refs": False,
            }
            if "delivery_state" in picking._fields:
                cancel_vals["delivery_state"] = "canceled_shipment"
            picking.write(cancel_vals)
            picking.message_post(
                body=_("Dachser shipment cancelled and unlinked from picking.")
            )

    def dachser_get_return_label(
        self, pickings, tracking_number=None, origin_date=None
    ):
        """Generate a return label by swapping consignor and consignee."""
        client = self._dachser_get_client()
        for picking in pickings:
            partner = picking.partner_id
            shipper_partner = (
                picking.picking_type_id.warehouse_id.partner_id
                or picking.company_id.partner_id
                or self.env.company.partner_id
            )
            ship_date = fields.Date.to_string(
                origin_date or fields.Date.context_today(self)
            )
            pkg_count = max(
                1,
                getattr(picking, "number_of_packages", 0)
                or picking.dachser_packages_qty
                or 1,
            )
            label_payload = {
                "format": (self.dachser_label_format or "P").upper(),
                "count": pkg_count,
                "fontFileName": (self.dachser_font_file_name or "ARIALR.FNT").strip(),
                "labelTypes": self._dachser_get_label_types_list(),
                "shipment": {
                    "division": self.dachser_division or "T",
                    "product": self._dachser_get_product_code(),
                    "shipmentDate": ship_date,
                    "forwarder": {"id": (self.dachser_forwarder_id or "193").strip()},
                    "consignor": self._dachser_build_partner_payload(
                        partner, include_id=False, is_consignor=False, minimal=False
                    ),
                    "consignee": self._dachser_build_partner_payload(
                        shipper_partner,
                        include_id=True,
                        is_consignor=True,
                        minimal=False,
                    ),
                    "references": [
                        {"code": "100", "value": f"RET-{picking.name}"[:35]}
                    ],
                },
            }
            lbl_resp = client.generate_standalone_label(label_payload)
            ssccs = lbl_resp.get("ssccs") or []
            label_b64 = lbl_resp.get("label") or False
            ret_ref = ssccs[0] if ssccs else f"RET-{picking.name}"
            attachment = self._dachser_attach_label_to_picking(
                picking=picking,
                label_b64=label_b64,
                tracking_ref=ret_ref,
                is_return=True,
            )
            picking.message_post(
                body=_("Dachser return label generated (SSCC: %s).")
                % (", ".join(ssccs) or ret_ref),
                attachment_ids=[attachment.id] if attachment else [],
            )

    # =========================================================================
    # ADVANCED ACTIONS ON PICKING (TMS, LABELS, TRACKING, POD, COSTS, ROUTING)
    # =========================================================================
    def dachser_send_order_to_tms(self, picking):
        """Transmit an `imported` or `labelled` order to Dachser TMS."""
        self.ensure_one()
        if not picking.dachser_transport_order_id:
            raise UserError(
                _("Picking %s does not have a Dachser Transport Order ID.")
                % picking.name
            )
        client = self._dachser_get_client()
        resp = client.send_transport_order(picking.dachser_transport_order_id)
        new_state = resp.get("state") or "sent"
        label_b64 = resp.get("label")
        ssccs = resp.get("ssccs") or []

        vals = {"dachser_order_state": new_state}
        if "tracking_state_history" in picking._fields:
            vals["tracking_state_history"] = new_state
        if ssccs and not picking.dachser_sscc_refs:
            vals["dachser_sscc_refs"] = ", ".join(ssccs)
            if not picking.carrier_tracking_ref:
                vals["carrier_tracking_ref"] = ", ".join(ssccs)
        picking.write(vals)

        attachment = False
        if label_b64:
            attachment = self._dachser_attach_label_to_picking(
                picking,
                label_b64,
                picking.carrier_tracking_ref or picking.dachser_transport_order_id,
            )
        picking.message_post(
            body=_(
                "Transport order #%(id)s transmitted to Dachser TMS (state: %(state)s)."
            )
            % {"id": picking.dachser_transport_order_id, "state": new_state},
            attachment_ids=[attachment.id] if attachment else [],
        )
        return resp

    def dachser_fetch_labels(self, picking):
        """Reprint or download PDF/ZPL labels for an existing Dachser order."""
        self.ensure_one()
        client = self._dachser_get_client()
        if picking.dachser_transport_order_id:
            resp = client.get_transport_order_labels(
                order_id=picking.dachser_transport_order_id,
                label_format=self.dachser_label_format or "P",
                label_types=self._dachser_get_label_types_list(),
                font_file_name=self.dachser_font_file_name
                if self.dachser_label_format == "Z"
                else None,
            )
        else:
            shipper_partner = (
                picking.picking_type_id.warehouse_id.partner_id
                or picking.company_id.partner_id
                or self.env.company.partner_id
            )
            ship_date = fields.Date.to_string(
                picking.scheduled_date.date()
                if picking.scheduled_date
                else fields.Date.context_today(self)
            )
            existing_ssccs = [
                s.strip()
                for s in (picking.dachser_sscc_refs or "").split(",")
                if s.strip()
            ]
            pkg_count = max(
                1,
                getattr(picking, "number_of_packages", 0)
                or picking.dachser_packages_qty
                or 1,
            )
            label_payload = {
                "format": (self.dachser_label_format or "P").upper(),
                "count": pkg_count,
                "fontFileName": (self.dachser_font_file_name or "ARIALR.FNT").strip(),
                "labelTypes": self._dachser_get_label_types_list(),
                "shipment": {
                    "division": self.dachser_division or "T",
                    "product": self._dachser_get_product_code(),
                    "shipmentDate": ship_date,
                    "forwarder": {"id": (self.dachser_forwarder_id or "193").strip()},
                    "consignor": self._dachser_build_partner_payload(
                        shipper_partner,
                        include_id=True,
                        is_consignor=True,
                        minimal=False,
                    ),
                    "consignee": self._dachser_build_partner_payload(
                        picking.partner_id,
                        include_id=False,
                        is_consignor=False,
                        minimal=False,
                    ),
                    "references": self._dachser_build_references(picking),
                },
            }
            if existing_ssccs:
                label_payload["shipment"]["ssccs"] = existing_ssccs
            resp = client.generate_standalone_label(label_payload)

        label_b64 = resp.get("label")
        ssccs = resp.get("ssccs") or []
        if ssccs and not picking.dachser_sscc_refs:
            picking.dachser_sscc_refs = ", ".join(ssccs)
        if not picking.carrier_tracking_ref and ssccs:
            picking.carrier_tracking_ref = ", ".join(ssccs)

        attachment = self._dachser_attach_label_to_picking(
            picking,
            label_b64,
            (ssccs[0] if ssccs else picking.carrier_tracking_ref or picking.name),
        )
        if attachment:
            picking.message_post(
                body=_("Dachser label downloaded and attached to picking."),
                attachment_ids=[attachment.id],
            )
        return attachment

    @staticmethod
    def _dachser_normalize_shipment_items(raw_data):
        if isinstance(raw_data, dict) and "shipments" in raw_data:
            return raw_data.get("shipments", [])
        if isinstance(raw_data, list):
            return raw_data
        return []

    @staticmethod
    def _dachser_extract_latest_event(status_block):
        if isinstance(status_block, list):
            latest_event = status_block[-1] if status_block else {}
            for st in status_block:
                if isinstance(st, dict) and st.get("statusSequence") == 1:
                    latest_event = st
                    break
        elif isinstance(status_block, dict):
            latest_event = status_block
        else:
            latest_event = {}

        event_obj = (
            latest_event.get("event")
            if isinstance(latest_event.get("event"), dict)
            else latest_event
        )
        event_code = str(event_obj.get("code") or "")
        event_desc = event_obj.get("description") or ""
        event_date = (
            latest_event.get("date")
            or latest_event.get("statusDate")
            or event_obj.get("date")
            or ""
        )
        event_loc = latest_event.get("location") or event_obj.get("location") or ""
        reason_desc = (
            latest_event.get("reasonDescription")
            or event_obj.get("reasonDescription")
            or ""
        )
        return (
            latest_event,
            event_code,
            event_desc,
            event_date,
            event_loc,
            reason_desc,
        )

    @staticmethod
    def _dachser_format_tracking_history(history_items, status_block, latest_event):
        history_lines = []
        oca_history_lines = []
        hist_source = (
            history_items[-1].get("status", [])
            if history_items
            else (status_block if isinstance(status_block, list) else [])
        )
        if isinstance(hist_source, dict):
            hist_source = [hist_source]
        elif not hist_source and latest_event:
            hist_source = [latest_event]

        # Reverse descending statusSequence to chronological order
        if (
            len(hist_source) > 1
            and isinstance(hist_source[0], dict)
            and "statusSequence" in hist_source[0]
        ):
            hist_source = list(reversed(hist_source))

        for ev in hist_source:
            ev_inner = ev.get("event") if isinstance(ev.get("event"), dict) else ev
            ev_dt = ev.get("date") or ev.get("statusDate") or ev_inner.get("date") or ""
            ev_code = ev_inner.get("code") or ""
            ev_desc = ev_inner.get("description") or ""
            ev_loc = ev.get("location") or ev_inner.get("location") or ""
            ev_reason = (
                ev.get("reasonDescription") or ev_inner.get("reasonDescription") or ""
            )
            line_str = f"[{ev_dt}] ({ev_code}) {ev_desc}"
            if ev_loc:
                line_str += f" — {ev_loc}"
            if ev_reason:
                line_str += f" ({ev_reason})"
            history_lines.append(line_str)
            oca_history_lines.append(f"- {ev_dt}: [{ev_code}] {ev_desc}")
        return history_lines, oca_history_lines

    def dachser_update_tracking_state(self, picking):
        """Query current shipment status (`/rest/v2/shipmentstatus`) and full
        event history (`/rest/v2/shipmenthistory`) from Dachser and update
        both detailed Dachser fields and OCA `delivery_state` fields.
        """
        self.ensure_one()
        client = self._dachser_get_client()
        tracking_ref = (
            (picking.dachser_consignment_id or "")
            or str(picking.carrier_tracking_ref or "").split(",")[0].strip()
            or picking.name
        )
        if not tracking_ref:
            raise UserError(
                _("No tracking reference found on picking %s.") % picking.name
            )

        status_raw = client.get_shipment_status(
            tracking_number=tracking_ref,
            customer_id=self.dachser_consignor_id or None,
        )
        history_raw = []
        try:
            history_raw = client.get_shipment_history(
                tracking_number=tracking_ref,
                customer_id=self.dachser_consignor_id or None,
            )
        except Exception as exc:
            _logger.debug(
                "Could not retrieve shipmenthistory for %s: %s", tracking_ref, exc
            )

        status_items = self._dachser_normalize_shipment_items(status_raw)
        history_items = self._dachser_normalize_shipment_items(history_raw)

        if not status_items and not history_items:
            raise UserError(
                _(
                    "Dachser has not returned any tracking events yet for "
                    "reference '%s'."
                )
                % tracking_ref
            )

        info = (status_items[-1] if status_items else history_items[-1]) or {}
        consignment_id = (
            info.get("consignmentId") or picking.dachser_consignment_id or False
        )
        pod_signor = info.get("podSignor") or picking.dachser_pod_signor or False
        status_block = info.get("status")

        (
            latest_event,
            event_code,
            event_desc,
            event_date,
            event_loc,
            reason_desc,
        ) = self._dachser_extract_latest_event(status_block)
        history_lines, oca_history_lines = self._dachser_format_tracking_history(
            history_items, status_block, latest_event
        )

        mapped_state = map_dachser_status_to_state(event_code, event_desc)
        mapped_delivery_state = map_dachser_status_to_delivery_state(
            event_code, event_desc
        )
        full_status_desc = event_desc
        if event_loc:
            full_status_desc += f" ({event_loc})"
        if reason_desc:
            full_status_desc += f" - {reason_desc}"

        vals = {
            "dachser_consignment_id": consignment_id,
            "dachser_status_code": event_code,
            "dachser_status_description": full_status_desc,
            "dachser_status_date": event_date,
            "dachser_pod_signor": pod_signor,
            "dachser_shipment_state": mapped_state,
            "dachser_tracking_history": "\n".join(history_lines)
            if history_lines
            else full_status_desc,
        }
        # Populate OCA `delivery_state` fields
        if "delivery_state" in picking._fields:
            vals["delivery_state"] = mapped_delivery_state
        if "tracking_state" in picking._fields:
            vals["tracking_state"] = event_desc or full_status_desc
        if "tracking_state_history" in picking._fields:
            vals["tracking_state_history"] = (
                "\n".join(oca_history_lines) if oca_history_lines else full_status_desc
            )
        if "tracking_json" in picking._fields:
            vals["tracking_json"] = history_raw or status_raw
        if (
            "date_delivered" in picking._fields
            and mapped_delivery_state == "customer_delivered"
            and not picking.date_delivered
        ):
            vals["date_delivered"] = fields.Datetime.now()

        picking.write(vals)
        return info

    def dachser_tracking_state_update(self, picking):
        """OCA `delivery_state` hook called by `picking.tracking_state_update()`."""
        self.ensure_one()
        if not picking.carrier_tracking_ref and not picking.dachser_consignment_id:
            return
        return self.dachser_update_tracking_state(picking)

    def dachser_fetch_pod(self, picking):
        """Download signed Proof of Delivery (POD PDF) from `/rest/v2/pods`,
        attach it to the picking, and populate OCA `pod_file` fields.
        """
        self.ensure_one()
        client = self._dachser_get_client()
        tracking_ref = (
            (picking.dachser_consignment_id or "")
            or str(picking.carrier_tracking_ref or "").split(",")[0].strip()
            or picking.name
        )
        pods = client.get_pod(
            tracking_number=tracking_ref,
            customer_id=self.dachser_consignor_id or None,
        )
        if not pods:
            raise UserError(
                _("No Proof of Delivery (POD) is available yet for reference '%s'.")
                % tracking_ref
            )

        pod_entry = pods[0]
        pod_b64 = pod_entry.get("podDocument")
        if not pod_b64:
            raise UserError(
                _("Dachser returned the POD record without an attached PDF document.")
            )

        consignment_id = pod_entry.get("consignmentId") or tracking_ref
        archive_date = pod_entry.get("archiveDate") or ""
        filename = f"Dachser_POD_{consignment_id}.pdf"
        encoded_datas = pod_b64.encode("ascii") if isinstance(pod_b64, str) else pod_b64
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": filename,
                    "datas": encoded_datas,
                    "res_model": "stock.picking",
                    "res_id": picking.id,
                    "mimetype": "application/pdf",
                }
            )
        )
        pod_vals = {
            "dachser_pod_received": True,
            "dachser_consignment_id": pod_entry.get("consignmentId")
            or picking.dachser_consignment_id,
        }
        if "pod_file" in picking._fields:
            pod_vals["pod_file"] = encoded_datas
        if "pod_filename" in picking._fields:
            pod_vals["pod_filename"] = filename
        if "pod_error" in picking._fields:
            pod_vals["pod_error"] = False
        picking.write(pod_vals)

        picking.message_post(
            body=_(
                "Proof of Delivery (POD) downloaded from Dachser "
                "(Consignment: %(cid)s, Archive date: %(dt)s)."
            )
            % {"cid": consignment_id, "dt": archive_date or "N/A"},
            attachment_ids=[attachment.id],
        )
        return attachment

    def dachser_fetch_freight_costs(self, picking):
        """Query actual invoiced freight costs (`/rest/v2/freightcosts`) to
        audit deviations against the initial estimated cost on the picking.
        """
        self.ensure_one()
        client = self._dachser_get_client()
        tracking_ref = (
            (picking.dachser_consignment_id or "")
            or str(picking.carrier_tracking_ref or "").split(",")[0].strip()
            or picking.name
        )
        costs_list = client.get_freight_costs(
            tracking_number=tracking_ref,
            customer_id=self.dachser_consignor_id or None,
        )
        if not costs_list:
            raise UserError(
                _(
                    "Dachser does not have invoiced freight costs yet for "
                    "reference '%s'."
                )
                % tracking_ref
            )

        item = costs_list[0]
        total_block = item.get("totalAmount") or {}
        invoiced_amount = float(total_block.get("amount") or 0.0)
        currency_code = total_block.get("currency") or "EUR"
        invoice_number = item.get("invoiceNumber") or ""
        invoice_date = item.get("invoiceDate") or False

        cw_block = item.get("chargableWeight") or {}
        chargeable_weight = float(
            cw_block.get("weight") or picking.dachser_chargeable_weight or 0.0
        )

        details_lines = []
        for det in item.get("costsDetails") or []:
            stype = det.get("serviceType") or ""
            sdesc = det.get("serviceTypeDescription") or stype
            samount_block = det.get("serviceTypeAmount") or {}
            samount = float(samount_block.get("amount") or 0.0)
            scurr = samount_block.get("currency") or currency_code
            details_lines.append(f"• [{stype}] {sdesc}: {samount:.2f} {scurr}")

        header_str = _(
            "Dachser Invoice #%(inv)s (%(dt)s): %(amt).2f %(curr)s | "
            "Chargeable weight: %(chg).2f kg"
        ) % {
            "inv": invoice_number or "Pending",
            "dt": invoice_date or "N/A",
            "amt": invoiced_amount,
            "curr": currency_code,
            "chg": chargeable_weight,
        }
        breakdown_str = header_str + (
            "\n" + "\n".join(details_lines) if details_lines else ""
        )

        vals = {
            "dachser_invoiced_cost": invoiced_amount,
            "dachser_invoice_number": invoice_number,
            "dachser_chargeable_weight": chargeable_weight,
            "dachser_cost_breakdown": breakdown_str,
            "dachser_consignment_id": item.get("consignmentNumber")
            or picking.dachser_consignment_id,
        }
        if invoice_date:
            try:
                vals["dachser_invoice_date"] = invoice_date[:10]
            except Exception as exc:
                _logger.debug(
                    "Invalid Dachser invoiceDate %r on picking %s: %s",
                    invoice_date,
                    picking.name,
                    exc,
                )
        picking.write(vals)

        diff = invoiced_amount - (picking.dachser_estimated_cost or 0.0)
        picking.message_post(
            body=Markup(
                "<p><b>%s</b></p>"
                "<ul>"
                "<li><b>%s:</b> %.2f %s</li>"
                "<li><b>%s:</b> %.2f € (%+.2f €)</li>"
                "<li><b>%s:</b> %s (%s)</li>"
                "<li><b>%s:</b> %.2f kg</li>"
                "</ul>"
            )
            % (
                _("Dachser Invoiced Freight Costs updated:"),
                _("Invoiced Amount"),
                invoiced_amount,
                currency_code,
                _("Initial Estimated Cost"),
                picking.dachser_estimated_cost or 0.0,
                diff,
                _("Dachser Invoice Number"),
                invoice_number or "N/A",
                invoice_date or "N/A",
                _("Chargeable Weight"),
                chargeable_weight,
            )
        )
        return item

    def dachser_check_routing(self, picking):
        """Query Dachser LDR routing (`/rest/v2/routings`) for destination."""
        self.ensure_one()
        client = self._dachser_get_client()
        shipper_partner = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
            or self.env.company.partner_id
        )
        partner = picking.partner_id
        ship_date = fields.Date.to_string(
            picking.scheduled_date.date()
            if picking.scheduled_date
            else fields.Date.context_today(self)
        )
        resp = client.get_routing(
            shipment_date=ship_date,
            division=self.dachser_division or "T",
            product=self._dachser_get_product_code(),
            forwarder_id=(self.dachser_forwarder_id or "193").strip(),
            consignor_country=(shipper_partner.country_id.code or "ES").upper(),
            consignor_zip=(shipper_partner.zip or "00000").strip(),
            consignor_city=(shipper_partner.city or "City").strip(),
            consignee_country=(partner.country_id.code or "ES").upper(),
            consignee_zip=(partner.zip or "00000").strip(),
            consignee_city=(partner.city or "City").strip(),
        )
        ldr_str = (
            resp.get("printableRelation")
            or resp.get("relationCode")
            or (resp.get("relation") or {}).get("printableRelation")
            or str(resp)
        )
        picking.dachser_ldr_routing = ldr_str
        picking.message_post(body=_("Dachser LDR routing verified: %s") % ldr_str)
        return resp

    def action_open_transfer_list_wizard(self):
        """Open the wizard to download the Daily Manifest (Transfer List) PDF."""
        self.ensure_one()
        return {
            "name": _("Download Dachser Daily Manifest (Transfer List)"),
            "type": "ir.actions.act_window",
            "res_model": "dachser.transfer.list.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_carrier_id": self.id,
                "default_order_date": fields.Date.context_today(self),
            },
        }
