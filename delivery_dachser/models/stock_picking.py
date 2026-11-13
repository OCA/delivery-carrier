# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .dachser_master_data import (
    DACHSER_DELIVERY_NOTICE_TYPES,
    DACHSER_SHIPMENT_STATES,
)

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_dachser_carrier = fields.Boolean(
        compute="_compute_is_dachser_carrier",
        store=True,
    )

    # =========================================================================
    # DACHSER SHIPMENT & TRANSPORT ORDER FIELDS
    # =========================================================================
    dachser_transport_order_id = fields.Char(
        string="Dachser Order ID",
        copy=False,
        index=True,
        help="Unique order identifier returned by POST /rest/v2/transportorders.",
    )
    dachser_order_state = fields.Selection(
        selection=[
            ("imported", "Draft in eLogistics (Imported)"),
            ("labelled", "Labelled in eLogistics (Labelled)"),
            ("sent", "Transmitted to Dachser TMS (Sent)"),
            ("cancelled", "Cancelled"),
        ],
        copy=False,
    )
    dachser_shipment_state = fields.Selection(
        selection=DACHSER_SHIPMENT_STATES,
        string="Dachser Tracking State",
        copy=False,
        index=True,
    )
    dachser_consignment_id = fields.Char(
        string="Dachser Consignment Number",
        copy=False,
        index=True,
        help="Official consignment number assigned by Dachser TMS.",
    )
    dachser_sscc_refs = fields.Char(
        string="SSCC License Plates (NVE)",
        copy=False,
        help=(
            "List of 18-digit SSCC codes generated for the packages/pallets "
            "of this picking."
        ),
    )
    dachser_ldr_routing = fields.Char(
        string="Dachser LDR Route Code",
        copy=False,
        help="LDR routing code between Dachser branches.",
    )
    dachser_tracking_url = fields.Char(
        string="Dachser Tracking Link",
        compute="_compute_dachser_tracking_url",
    )

    # =========================================================================
    # PER-PICKING OPERATIONAL OVERRIDES BEFORE SENDING TO DACHSER
    # =========================================================================
    dachser_packages_qty = fields.Integer(
        string="Dachser Packages / Pallets Qty",
        default=1,
        copy=False,
        help=(
            "Number of packages or pallets to declare in Dachser when detailed "
            "packages are not used in operations."
        ),
    )
    dachser_package_type_id = fields.Many2one(
        comodel_name="stock.package.type",
        string="Dachser Packaging Type",
        domain="[('package_carrier_type', '=', 'dachser')]",
        copy=False,
        help=(
            "Override the pallet/package type (Euro Pallet, Half Pallet, "
            "Carton...) for this specific picking."
        ),
    )
    dachser_content_override = fields.Char(
        string="Goods Description (Dachser)",
        size=20,
        copy=False,
        help=(
            "Goods description (max. 20 characters). If left empty, uses the "
            "delivery method default."
        ),
    )
    dachser_tail_lift = fields.Boolean(
        string="Requires Tail-Lift",
        copy=False,
    )
    dachser_fixed_delivery_date = fields.Date(
        string="Fixed Delivery Date (targofix)",
        copy=False,
        help="Committed delivery date (applicable to targofix / fixed-date services).",
    )
    dachser_delivery_notice_type = fields.Selection(
        selection=DACHSER_DELIVERY_NOTICE_TYPES,
        string="Delivery Notice",
        default="none",
        copy=False,
    )
    dachser_driver_notes = fields.Char(
        string="Delivery / Driver Instructions",
        size=70,
        copy=False,
        help="Free text instruction sent to Dachser with qualifier code ZU.",
    )

    # =========================================================================
    # ESTIMATED TARIFF VS ACTUAL INVOICED FREIGHT COST BY DACHSER
    # =========================================================================
    dachser_estimated_cost = fields.Float(
        string="Estimated Dachser Cost (€)",
        digits="Product Price",
        copy=False,
        help=(
            "Estimated shipping cost calculated via Dachser Quotation API "
            "or Local Tariff Table."
        ),
    )
    dachser_invoiced_cost = fields.Float(
        string="Invoiced Dachser Cost (€)",
        digits="Product Price",
        copy=False,
        help=(
            "Actual net freight cost invoiced by Dachser retrieved via "
            "/rest/v2/freightcosts."
        ),
    )
    dachser_cost_difference = fields.Float(
        string="Cost Deviation (€)",
        digits="Product Price",
        compute="_compute_dachser_cost_difference",
        store=True,
        help=(
            "Difference between the actual amount invoiced by Dachser and "
            "the initial estimated cost."
        ),
    )
    dachser_chargeable_weight = fields.Float(
        string="Dachser Chargeable Weight (kg)",
        copy=False,
    )
    dachser_invoice_number = fields.Char(
        copy=False,
    )
    dachser_invoice_date = fields.Date(
        copy=False,
    )
    dachser_cost_breakdown = fields.Text(
        string="Dachser Tariff / Cost Breakdown",
        copy=False,
    )

    # =========================================================================
    # REAL-TIME STATUS, EVENT HISTORY & PROOF OF DELIVERY (POD)
    # =========================================================================
    dachser_status_code = fields.Char(
        string="Latest Event Code",
        copy=False,
    )
    dachser_status_description = fields.Char(
        string="Latest Dachser Event",
        copy=False,
    )
    dachser_status_date = fields.Char(
        string="Latest Event Date/Time",
        copy=False,
    )
    dachser_pod_signor = fields.Char(
        string="POD Recipient / Signatory",
        copy=False,
    )
    dachser_pod_received = fields.Boolean(
        string="POD Downloaded",
        default=False,
        copy=False,
    )
    dachser_tracking_history = fields.Text(
        copy=False,
    )

    # =========================================================================
    # COMPUTE & ONCHANGE METHODS
    # =========================================================================
    @api.depends("carrier_id", "carrier_id.delivery_type")
    def _compute_is_dachser_carrier(self):
        for picking in self:
            picking.is_dachser_carrier = bool(
                picking.carrier_id and picking.carrier_id.delivery_type == "dachser"
            )

    @api.depends("dachser_estimated_cost", "dachser_invoiced_cost")
    def _compute_dachser_cost_difference(self):
        for picking in self:
            if picking.dachser_invoiced_cost:
                picking.dachser_cost_difference = picking.dachser_invoiced_cost - (
                    picking.dachser_estimated_cost or 0.0
                )
            else:
                picking.dachser_cost_difference = 0.0

    @api.depends("carrier_id", "carrier_tracking_ref", "dachser_consignment_id")
    def _compute_dachser_tracking_url(self):
        for picking in self:
            if (
                picking.carrier_id
                and picking.carrier_id.delivery_type == "dachser"
                and (picking.carrier_tracking_ref or picking.dachser_consignment_id)
            ):
                picking.dachser_tracking_url = (
                    picking.carrier_id.dachser_get_tracking_link(picking)
                )
            else:
                picking.dachser_tracking_url = False

    @api.onchange("number_of_packages")
    def _onchange_number_of_packages_sync_dachser(self):
        for picking in self:
            if picking.number_of_packages and picking.number_of_packages > 0:
                picking.dachser_packages_qty = picking.number_of_packages

    @api.onchange("dachser_packages_qty")
    def _onchange_dachser_packages_qty_sync_number(self):
        for picking in self:
            if (
                "number_of_packages" in picking._fields
                and picking.dachser_packages_qty
                and picking.dachser_packages_qty > 0
            ):
                picking.number_of_packages = picking.dachser_packages_qty

    @api.onchange("partner_id", "carrier_id")
    def _onchange_partner_dachser_defaults(self):
        for picking in self:
            if (
                picking.carrier_id
                and picking.carrier_id.delivery_type == "dachser"
                and picking.partner_id
            ):
                picking.dachser_tail_lift = (
                    picking.partner_id.dachser_tail_lift
                    or picking.carrier_id.dachser_delivery_tail_lift
                )
                if (
                    picking.partner_id.dachser_delivery_notice_type
                    and picking.partner_id.dachser_delivery_notice_type != "none"
                ):
                    picking.dachser_delivery_notice_type = (
                        picking.partner_id.dachser_delivery_notice_type
                    )
                else:
                    picking.dachser_delivery_notice_type = (
                        picking.carrier_id.dachser_delivery_notice_type
                    )

    # =========================================================================
    # ACTION BUTTONS ON PICKING
    # =========================================================================
    def _ensure_dachser_carrier(self):
        self.ensure_one()
        if not self.carrier_id or self.carrier_id.delivery_type != "dachser":
            raise UserError(
                _("Picking %s does not have a Dachser delivery method assigned.")
                % self.name
            )
        return self.carrier_id

    def action_dachser_send_to_tms(self):
        """Transmit an order previously created as `imported` or `labelled`
        to Dachser TMS.
        """
        for picking in self:
            carrier = picking._ensure_dachser_carrier()
            carrier.dachser_send_order_to_tms(picking)
        return True

    def action_dachser_get_label(self):
        """Download or reprint Dachser PDF/ZPL labels for this picking."""
        for picking in self:
            carrier = picking._ensure_dachser_carrier()
            carrier.dachser_fetch_labels(picking)
        return True

    def action_dachser_update_status(self):
        """Update live tracking status and event history from Dachser API v2."""
        for picking in self:
            carrier = picking._ensure_dachser_carrier()
            carrier.dachser_update_tracking_state(picking)
        return True

    def action_dachser_get_pod(self):
        """Download signed Proof of Delivery (POD PDF) for this picking."""
        for picking in self:
            carrier = picking._ensure_dachser_carrier()
            carrier.dachser_fetch_pod(picking)
        return True

    def action_dachser_fetch_freight_costs(self):
        """Query actual invoiced freight costs from Dachser
        (`/rest/v2/freightcosts`) for this picking.
        """
        for picking in self:
            carrier = picking._ensure_dachser_carrier()
            carrier.dachser_fetch_freight_costs(picking)
        return True

    def action_dachser_check_routing(self):
        """Verify LDR routing (`/rest/v2/routings`) for the consignee address."""
        for picking in self:
            carrier = picking._ensure_dachser_carrier()
            carrier.dachser_check_routing(picking)
        return True

    def action_dachser_calculate_rate(self):
        """Calculate or recalculate estimated shipping cost from the picking."""
        for picking in self:
            carrier = picking._ensure_dachser_carrier()
            partner = picking.partner_id
            if not partner or not partner.country_id or not partner.zip:
                raise UserError(
                    _(
                        "The picking consignee must have a Postal Code and "
                        "Country to calculate the Dachser rate."
                    )
                )
            gross_weight_kg, total_vol_m3, total_ldm, packages_qty, order_lines = (
                carrier._dachser_prepare_picking_lines(picking)
            )
            chargeable_weight_kg = carrier._dachser_compute_chargeable_weight(
                gross_weight_kg=gross_weight_kg,
                volume_m3=total_vol_m3,
                ldm=total_ldm,
            )
            term_code = carrier._dachser_get_term_code(picking=picking)
            transport_options, tail_lift, notice_type = (
                carrier._dachser_build_transport_options(partner, picking=picking)
            )

            cost = None
            breakdown = ""
            if carrier.dachser_rate_mode in ("api_quotation", "api_with_fallback"):
                try:
                    api_cost, _curr, _qid, api_breakdown = (
                        carrier._dachser_rate_from_quotation_api(
                            partner=partner,
                            order_lines=order_lines,
                            term_code=term_code,
                            transport_options=transport_options,
                            reference_value=picking.name,
                        )
                    )
                    if api_cost > 0:
                        cost = api_cost
                        breakdown = api_breakdown
                except UserError:
                    if carrier.dachser_rate_mode == "api_quotation":
                        raise

            if cost is None:
                table_cost, table_breakdown, _rule = (
                    carrier._dachser_rate_from_tariff_table(
                        partner=partner,
                        chargeable_weight_kg=chargeable_weight_kg,
                        packages_qty=packages_qty,
                        tail_lift=tail_lift,
                        notice_type=notice_type,
                    )
                )
                if table_cost is None:
                    raise UserError(
                        _(
                            "No applicable Dachser tariff found for "
                            "%(partner)s (ZIP %(zip)s, %(weight).2f "
                            "chargeable kg, %(pkgs)d packages)."
                        )
                        % {
                            "partner": partner.display_name,
                            "zip": partner.zip,
                            "weight": chargeable_weight_kg,
                            "pkgs": packages_qty,
                        }
                    )
                cost = table_cost
                breakdown = table_breakdown

            summary_line = _(
                "Gross weight: %(gross).2f kg | Vol: %(vol).3f m³ | "
                "Chargeable weight: %(chg).2f kg | Packages: %(pkgs)d"
            ) % {
                "gross": gross_weight_kg,
                "vol": total_vol_m3,
                "chg": chargeable_weight_kg,
                "pkgs": packages_qty,
            }
            picking.write(
                {
                    "dachser_estimated_cost": cost,
                    "dachser_chargeable_weight": chargeable_weight_kg,
                    "dachser_cost_breakdown": f"{breakdown}\n{summary_line}",
                }
            )
        return True

    def action_open_dachser_tracking_url(self):
        """Open the Dachser eLogistics tracking link in a new browser tab."""
        self.ensure_one()
        if not self.dachser_tracking_url:
            raise UserError(
                _("This picking does not have a Dachser tracking link yet.")
            )
        return {
            "type": "ir.actions.act_url",
            "url": self.dachser_tracking_url,
            "target": "new",
        }

    # =========================================================================
    # SCHEDULED ACTION (CRON): AUTOMATIC STATUS, POD & INVOICED COSTS UPDATE
    # =========================================================================
    @api.model
    def _cron_dachser_update_shipments(self):
        """Scheduled cron job that updates active Dachser shipment statuses,
        downloads POD when delivered, and retrieves actual invoiced freight costs.
        """
        date_limit = fields.Datetime.now() - timedelta(days=45)
        pickings = self.search(
            [
                ("is_dachser_carrier", "=", True),
                ("state", "=", "done"),
                ("carrier_tracking_ref", "!=", False),
                ("date_done", ">=", date_limit),
                "|",
                ("dachser_shipment_state", "not in", ("delivered", "cancelled")),
                ("dachser_invoiced_cost", "=", 0.0),
            ],
            limit=80,
        )

        for picking in pickings:
            try:
                if picking.dachser_shipment_state != "delivered":
                    picking.carrier_id.dachser_update_tracking_state(picking)
                if (
                    picking.dachser_shipment_state == "delivered"
                    and not picking.dachser_pod_received
                ):
                    try:
                        picking.carrier_id.dachser_fetch_pod(picking)
                    except Exception as pod_exc:
                        _logger.debug(
                            "POD not yet available for %s: %s", picking.name, pod_exc
                        )
                if not picking.dachser_invoiced_cost:
                    try:
                        picking.carrier_id.dachser_fetch_freight_costs(picking)
                    except Exception as cost_exc:
                        _logger.debug(
                            "Invoiced costs not yet available for %s: %s",
                            picking.name,
                            cost_exc,
                        )
            except Exception as exc:
                _logger.warning(
                    "Automatic Dachser update error for picking %s: %s",
                    picking.name,
                    exc,
                )
