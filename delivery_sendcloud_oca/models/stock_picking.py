# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import json
import logging
import uuid
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_repr, float_round
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "sendcloud.mixin"]

    sendcloud_parcel_ids = fields.One2many("sendcloud.parcel", "picking_id")
    sendcloud_parcel_count = fields.Integer(
        string="Parcels", compute="_compute_sendcloud_parcel_count"
    )
    sendcloud_shipment_uuid = fields.Char(copy=False)
    sendcloud_last_cached = fields.Datetime(copy=False, readonly=True)
    sendcloud_announce = fields.Boolean(
        default=True, help="Should the parcel request a label."
    )
    sendcloud_is_return = fields.Boolean()
    sendcloud_insured_value = fields.Float(
        help="Insured Value must be in Euro currency."
    )
    sendcloud_shipping_method_checkout_name = fields.Char()
    sendcloud_apply_shipping_rules = fields.Boolean(
        help="When set to True configured shipping rules will be applied before "
        "creating the label and announcing the Parcel"
    )
    sendcloud_service_point_required = fields.Boolean(
        related="carrier_id.sendcloud_service_point_required"
    )
    sendcloud_customs_shipment_type = fields.Selection(
        selection="_get_sendcloud_customs_shipment_type",
        compute="_compute_sendcloud_customs_shipment_type",
        readonly=False,
        store=True,
    )
    sendcloud_service_point_address = fields.Text(
        compute="_compute_sendcloud_service_point_address", readonly=False, store=True
    )
    sendcloud_shipment_code = fields.Char(index=True, copy=False)
    sendcloud_sp_details = fields.Char(compute="_compute_sendcloud_sp_details")

    label_print_status = fields.Selection(
        [
            ("generated", "Generated"),
            ("printed", "Printed"),
            ("partial", "Partially Printed"),
        ],
        compute="_compute_label_print_status",
        store=True,
    )

    @api.depends("sendcloud_parcel_ids", "sendcloud_parcel_ids.label_print_status")
    def _compute_label_print_status(self):
        for picking in self.filtered(lambda x: x.sendcloud_parcel_ids):
            if all(
                parcel.label_print_status == "generated"
                for parcel in picking.sendcloud_parcel_ids
            ):
                picking.label_print_status = "generated"
            elif all(
                parcel.label_print_status == "printed"
                for parcel in picking.sendcloud_parcel_ids
            ):
                picking.label_print_status = "printed"
            else:
                picking.label_print_status = "partial"
        for picking in self.filtered(lambda x: not x.sendcloud_parcel_ids):
            picking.label_print_status = None

    @api.depends(
        "carrier_id.sendcloud_integration_id",
        "carrier_id.sendcloud_carrier",
        "partner_id.country_id.code",
        "partner_id.zip",
    )
    def _compute_sendcloud_sp_details(self):
        user_lang = self.env.user.lang.replace("_", "-").lower()
        available_languages = [
            "en-us",
            "de-de",
            "en-gb",
            "es-es",
            "fr-fr",
            "it-it",
            "nl-nl",
        ]
        for picking in self:
            vals = {
                "api_key": picking.carrier_id.sendcloud_integration_id.public_key,
                "country": picking.partner_id.country_id.code
                and picking.partner_id.country_id.code.lower()
                or "",
                "postalcode": picking.partner_id.zip or "",
                "language": user_lang if user_lang in available_languages else "en-us",
                "carrier": picking.carrier_id.sendcloud_carrier or "",
            }
            picking.sendcloud_sp_details = json.dumps(vals)

    @api.depends("sale_id.sendcloud_customs_shipment_type", "sendcloud_is_return")
    def _compute_sendcloud_customs_shipment_type(self):
        for picking in self:
            shipment_type = picking.sendcloud_customs_shipment_type
            picking.sendcloud_customs_shipment_type = shipment_type
            sale_shipment_type = picking.sale_id.sendcloud_customs_shipment_type
            if not picking.sendcloud_is_return and sale_shipment_type:
                picking.sendcloud_customs_shipment_type = sale_shipment_type

    @api.depends("sale_id.sendcloud_service_point_address", "sendcloud_is_return")
    def _compute_sendcloud_service_point_address(self):
        for picking in self:
            service_point_address = picking.sendcloud_service_point_address
            picking.sendcloud_service_point_address = service_point_address
            sale_service_point_address = picking.sale_id.sendcloud_service_point_address
            if not picking.sendcloud_is_return and sale_service_point_address:
                picking.sendcloud_service_point_address = sale_service_point_address

    @api.depends("sendcloud_parcel_ids")
    def _compute_sendcloud_parcel_count(self):
        for picking in self:
            picking.sendcloud_parcel_count = len(picking.sendcloud_parcel_ids)

    # flake8: noqa: C901
    def _prepare_sendcloud_vals_from_picking(self, package=False):
        self.ensure_one()

        request_label = self.sendcloud_announce
        apply_shipping_rules = self.sendcloud_apply_shipping_rules
        is_return = False

        order = self.sale_id
        warehouse = self.picking_type_id.warehouse_id

        service_point_data = {}
        if self.sendcloud_service_point_required:
            if not self.sendcloud_service_point_address:
                raise ValidationError(_("Sendcloud Service Point is Required!"))

            service_point_data = json.loads(self.sendcloud_service_point_address)

        sender = self._get_sendcloud_recipient()

        vals = self.generate_sendcloud_ref_uuid_vals()
        if self.sendcloud_shipment_uuid:
            vals.update({"shipment_uuid": self.sendcloud_shipment_uuid})
        vals.update(
            {
                "created_at": self.create_date.isoformat(),
                "updated_at": self.write_date.isoformat(),
            }
        )
        # Recipient address details (mandatory)
        vals.update(
            {
                "name": sender.name or sender.display_name,
                "address": sender.street_name,
                "house_number": sender.street_number or "",
                "city": sender.city,
                "postal_code": sender.zip,
                "country": sender.country_id.code or "",
            }
        )
        if sender.street_number2:
            number_door = vals["house_number"] + " " + sender.street_number2
            vals["house_number"] = number_door

        # If sendcloud_auto_create_invoice, create invoice
        out_invoices = order._sendcloud_order_invoice()

        # Recipient address details (mandatory when shipping outside of EU)
        vals.update(
            {
                "country_state": sender.state_id.code or "",
                "customs_invoice_nr": out_invoices[-1].name if out_invoices else "",
                "customs_shipment_type": int(self.sendcloud_customs_shipment_type)
                if self.sendcloud_customs_shipment_type
                else None,
            }
        )
        vals.update({"to_state": sender.state_id.code or None})

        # Recipient address details (optional)
        vals.update(
            {
                "company_name": sender.name
                if sender.is_company
                else sender.parent_name or "",
                "address_2": sender.street2 or "",
            }
        )
        if order:
            vals.update(
                {
                    "currency": order.currency_id.name,
                }
            )
        if sender.mobile or sender.phone:
            vals.update({"telephone": sender.mobile or sender.phone})
        if sender.email:
            vals.update({"email": sender.email})
        elif sender.parent_id and sender.parent_id.email:
            vals.update({"email": sender.parent_id.email})
        vals.update({"to_post_number": service_point_data.get("postal_code", "")})
        if not warehouse.sencloud_sender_address_id:
            sender_address = self.env[
                "delivery.carrier"
            ]._get_default_sender_address_per_company(warehouse.company_id.id)
        else:
            sender_address = warehouse.sencloud_sender_address_id
        if sender_address:
            vals.update({"sender_address": sender_address.sendcloud_code})

        # Shipping service (optional)
        service_point_id = service_point_data.get("id")
        if service_point_id:
            service_point_id = int(service_point_data["id"])
        vals.update({"to_service_point": service_point_id})
        # TODO
        shipping_method_checkout_name = (
            self.sendcloud_shipping_method_checkout_name or ""
        )
        vals.update(
            {
                "shipping_method_checkout_name": shipping_method_checkout_name,
                "order_status": None,
                "payment_status": None,
            }
        )
        if self.sendcloud_insured_value:
            vals.update({"insured_value": self.sendcloud_insured_value or None})

        # Parcel properties (mandatory when shipping outside of EU)
        parcel_items = []
        move_lines = self.move_ids.mapped("move_line_ids")
        if package:
            move_lines = move_lines.filtered(
                lambda ml: ml.package_id == package or ml.result_package_id == package
            )
        else:
            move_lines = move_lines.filtered(
                lambda ml: not ml.package_id and not ml.result_package_id
            )
        if move_lines:
            moves = move_lines.mapped("move_id")
        else:
            moves = self.move_ids  # TODO should be never the case, raise an error?
        total_weight = 0.0
        for move in moves:
            line_vals = self._prepare_sendcloud_item_vals_from_moves(
                move, package=package
            )
            total_weight += line_vals["weight"]
            line_vals["weight"] = (
                line_vals["weight"] / line_vals["quantity"]
                if line_vals["quantity"]
                else 0.0
            )
            parcel_items += [line_vals]

        vals["parcel_items"] = parcel_items

        # Parcel properties (optional)
        if order.name:
            vals.update({"order_number": order.name})
        if total_weight:
            vals.update({"weight": total_weight})
        vals.update({"is_return": is_return})

        # Announcement (optional)
        vals.update({"request_label": request_label})

        # Announcement (required if request_label is True)
        vals.update(
            {
                "shipment": {"id": self.carrier_id.sendcloud_code},
                "apply_shipping_rules": apply_shipping_rules,
            }
        )
        return vals

    def _get_sendcloud_recipient(self):
        self.ensure_one()
        return self.partner_id or self.sale_id.partner_id

    def generate_sendcloud_ref_uuid_vals(self):
        self.ensure_one()
        order = self.sale_id
        if not order.sendcloud_order_code:
            force_order_code = self.env.context.get("force_sendcloud_order_code")
            order.sendcloud_order_code = force_order_code or uuid.uuid4()
        if not self.sendcloud_shipment_code:
            force_shipment_code = self.env.context.get("force_sendcloud_shipment_code")
            self.sendcloud_shipment_code = force_shipment_code or uuid.uuid4()
        return {
            "external_order_id": order.sendcloud_order_code,
            "external_shipment_id": self.sendcloud_shipment_code,
        }

    @api.model
    def _check_state_requires_hs_code(self, country_code, state_code):
        states = {"ES": ["TF", "GC"]}
        return country_code in states and state_code in states[country_code]

    def _prepare_sendcloud_item_vals_from_moves(self, move, package=False):
        self.ensure_one()

        weight = self._sendcloud_convert_weight_to_kg(move.weight)
        if not package:
            quantity = int(move.product_uom_qty)  # TODO should be quantity_done ?
        else:
            move_lines = move.move_line_ids.filtered(
                lambda ml: ml.result_package_id == package
            )
            if move_lines:
                quantity = sum(move_lines.mapped("quantity_product_uom"))
            else:
                quantity = sum(package.mapped("quant_ids.quantity"))

        partner_country = self.partner_id.country_id.code
        is_outside_eu = not self.partner_id.sendcloud_is_in_eu

        partner_state = self.partner_id.state_id.code
        state_requires_hs_code = self._check_state_requires_hs_code(
            partner_country, partner_state
        )

        price = move.sale_line_id.price_unit
        precision_digits = move.sale_line_id.currency_id.decimal_places
        if (
            hasattr(move, "bom_line_id")
            and move.bom_line_id
            and move.bom_line_id.bom_id.type == "phantom"
        ):
            # We want to compute each subproduct price based on the kit product price
            # and the total price of all components of the kit.Example.
            # Kitprice is 30€, it is made up of 3 subproducts costing 15€, 15€ and 10€.
            # Subproduct 1: Price ((15/40)*30) = 11,25€
            # Subproduct 2: Price ((15/40)*30) = 11,25€
            # Subproduct 3: Price ((10/40)*30) = 7,5€

            total_price = 0.0
            for line in move.bom_line_id.bom_id.bom_line_ids:
                if line._skip_bom_line(move.sale_line_id.product_id):
                    continue
                total_price += line.product_id.lst_price * line.product_qty

            subproduct = move.bom_line_id.product_id
            kit_product = move.sale_line_id.product_id
            if kit_product.lst_price:  # Prevent division by 0
                value = float_repr(
                    float_round(
                        (subproduct.lst_price / total_price) * price,
                        precision_digits=precision_digits,
                    ),
                    precision_digits=precision_digits,
                )
            else:
                value = 0
        else:
            value = float_repr(
                float_round(price, precision_digits=precision_digits),
                precision_digits=precision_digits,
            )

        # Parcel items (mandatory)
        line_vals = {
            "description": move.product_id.display_name,
            "quantity": quantity,
            "weight": weight,
            "value": value,
            # not converted to euro as the currency is always set
        }

        # Parcel items (mandatory when shipping outside of EU)
        if is_outside_eu or state_requires_hs_code:
            parcel_item_outside_eu = self._prepare_sendcloud_parcel_items_outside_eu(
                move
            )
            if not parcel_item_outside_eu.get("hs_code"):
                raise ValidationError(
                    _(
                        "Harmonized System Code is mandatory when shipping outside of "
                        "EU and to some states.\nYou should set the HS Code for "
                        "product %s"
                    )
                    % move.product_tmpl_id.name
                )
            if not parcel_item_outside_eu.get("origin_country"):
                raise ValidationError(
                    _(
                        "Origin Country is mandatory when shipping outside of EU and"
                        " to some states."
                    )
                )
            line_vals.update(parcel_item_outside_eu)
        # Parcel items (optional)
        if move.product_id.default_code:
            line_vals.update(
                {"sku": move.product_id.default_code}
            )  # TODO product.barcode or product.id
        line_vals.update({"product_id": ""})
        line_vals.update({"properties": {}})
        return line_vals

    def _prepare_sendcloud_parcel_items_outside_eu(self, move):
        self.ensure_one()
        product_tmplate = move.product_tmpl_id
        hs_code = product_tmplate.hs_code
        origin_country = product_tmplate.country_of_origin.code
        is_product_harmonized_system_installed = self.env["ir.module.module"].search(
            [("name", "=", "product_harmonized_system"), ("state", "=", "installed")],
            limit=1,
        )
        if is_product_harmonized_system_installed:
            # use field provided by OCA module "product_harmonized_system" if installed
            hs_code = product_tmplate.hs_code_id.hs_code
            origin_country = product_tmplate.origin_country_id.code or origin_country
        is_account_intrastat_installed = self.env["ir.module.module"].search(
            [("name", "=", "account_intrastat"), ("state", "=", "installed")], limit=1
        )
        if is_account_intrastat_installed:
            # use field provided by Enterprise module "account_intrastat" if installed
            hs_code = product_tmplate.intrastat_code_id.code or hs_code
            origin_country = (
                product_tmplate.intrastat_origin_country_id.code or origin_country
            )
        return {"hs_code": hs_code, "origin_country": origin_country}

    def _prepare_sendcloud_parcels_from_picking(self):
        self.ensure_one()

        vals_list = []

        # multicollo parcels (one collo is the master)
        colli = self.package_ids

        # in case only packages of a certain carrier should be considered
        # invoke this method passing "sendcloud_only_packs_with_carrier" in its context
        if self.env.context.get("sendcloud_only_packs_with_carrier"):
            packs_no_carrier = self._get_packs_no_carrier(colli)
            colli = colli - packs_no_carrier

        total_sendcloud_package_weight = 0.0
        for package in colli:
            weight = (
                package.shipping_weight
                or package.with_context(picking_id=self.id).weight
            )
            weight = self._sendcloud_convert_weight_to_kg(weight)
            weight = self._sendcloud_check_collo_weight(weight)
            total_sendcloud_package_weight += weight
            vals = self._prepare_sendcloud_vals_from_picking(package)
            vals["weight"] = weight
            vals["external_reference"] = self.name + "," + str(package.id)
            vals_list += [vals]

        if self.weight_bulk or (self.package_ids - colli) or not vals_list:
            weight = self._get_total_weight_bulk(total_sendcloud_package_weight)
            weight = self._sendcloud_convert_weight_to_kg(weight)
            weight = self._sendcloud_check_collo_weight(weight)
            vals = self._prepare_sendcloud_vals_from_picking()
            if vals:
                vals["weight"] = weight
                vals["external_reference"] = self.name + "," + str(0)
                vals_list += [vals]

        return vals_list

    def _sendcloud_check_collo_weight(self, weight):
        self.ensure_one()
        min_weight = self.carrier_id.sendcloud_min_weight
        max_weight = self.carrier_id.sendcloud_max_weight
        if min_weight and max_weight and not (min_weight <= weight <= max_weight):
            raise ValidationError(
                _(
                    "Sendcloud shipping method not compatible with selected packaging."
                    "\nPlease select a shipping method such that the collis' weights "
                    "are between Min Weight and Max Weight."
                )
            )
        return weight

    def _get_total_weight_bulk(self, total_sendcloud_package_weight):
        self.ensure_one()
        return (self.shipping_weight or self.weight) - total_sendcloud_package_weight

    @api.model
    def _get_packs_no_carrier(self, colli):
        return colli.filtered(
            lambda p: p.packaging_id.package_carrier_type in [False, "none"]
        )

    def action_open_sendcloud_parcels(self):
        self.ensure_one()
        if len(self.sendcloud_parcel_ids) == 1:
            return {
                "type": "ir.actions.act_window",
                "res_model": "sendcloud.parcel",
                "res_id": self.sendcloud_parcel_ids.id,
                "view_mode": "form",
                "context": self.env.context,
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Sendcloud Parcels"),
            "res_model": "sendcloud.parcel",
            "domain": [("id", "in", self.sendcloud_parcel_ids.ids)],
            "view_mode": "tree,form",
            "context": self.env.context,
        }

    def cancel_shipment(self):
        if (
            not self.env.context.get("do_sendcloud_cancel_shipment")
            and len(self) == 1
            and self.delivery_type == "sendcloud"
            and self.picking_type_code == "outgoing"
        ):
            action = "delivery_sendcloud_oca.sendcloud_cancel_shipment_confirm_wizard"
            return self.env.ref(action).read()[0]
        return super().cancel_shipment()

    def button_delete_sendcloud_picking(self):
        self.ensure_one()
        to_delete_shipments = self.to_delete_sendcloud_pickings()
        self.delete_sendcloud_pickings(to_delete_shipments)

    def to_delete_sendcloud_pickings(self):
        res = {}
        for picking in self.filtered(
            lambda p: p.delivery_type == "sendcloud"
            and p.carrier_id.delivery_type == "sendcloud"
            and p.picking_type_code == "outgoing"
        ):
            integration = picking.carrier_id.sendcloud_integration_id
            if picking.sendcloud_shipment_uuid:
                vals = {"shipment_uuid": picking.sendcloud_shipment_uuid}
                picking.with_context(
                    skip_sync_picking_to_sendcloud=True
                ).sendcloud_shipment_uuid = None
            else:
                vals = picking.generate_sendcloud_ref_uuid_vals()
            if integration.id not in res:
                res[integration.id] = []
            res[integration.id] += [vals]
        return res

    @api.model
    def delete_sendcloud_pickings(self, to_delete_shipments):
        for integration_id in to_delete_shipments:
            integration = self.env["sendcloud.integration"].browse(integration_id)
            vals_list = to_delete_shipments[integration_id]
            for vals in vals_list:
                response = integration.delete_shipments(
                    integration.sendcloud_code, vals
                )
                if response.get("error"):
                    picking_id = vals.get("external_shipment_id") or vals.get(
                        "shipment_uuid"
                    )
                    _logger.error(
                        "Sendcloud deleting picking %s error: %s",
                        picking_id,
                        response.get("error").get("message"),
                    )

    def action_download_sendcloud_labels(self):
        if self.mapped("sendcloud_parcel_ids").mapped("attachment_id"):
            return {
                "type": "ir.actions.act_url",
                "url": "/sendcloud/picking/download_labels?ids=%s"
                % (",".join([str(id) for id in self.ids])),
                "target": "self",
            }

    def action_multi_create_sendcloud_labels(self):
        for picking in self:
            picking.button_create_sendcloud_labels()

    def action_multi_create_sendcloud_labels_download(self):
        self.action_multi_create_sendcloud_labels()
        self.action_download_sendcloud_labels()

    def button_create_sendcloud_labels(self):
        self.ensure_one()
        if (
            self.picking_type_code == "outgoing"
            and self.delivery_type == "sendcloud"
            and self.sale_id
        ):
            integration = self.carrier_id.sendcloud_integration_id
            vals = self._prepare_sendcloud_parcels_from_picking()
            parcels_data = self._sendcloud_sync_multiple_parcels(integration, vals)
            self._sendcloud_create_update_received_parcels(
                parcels_data, integration.company_id.id
            )
            parcels = self.mapped("sendcloud_parcel_ids")
            parcels._generate_parcel_labels()
            return self.action_open_sendcloud_parcels()

    @api.model
    def _sendcloud_vals_triggering_sync(self):
        return [
            "sendcloud_announce",
            "sendcloud_is_return",
            "sendcloud_insured_value",
            "sendcloud_shipping_method_checkout_name",
            "sendcloud_apply_shipping_rules",
            "sendcloud_customs_shipment_type",
            "sendcloud_service_point_address",
            "partner_id",
            "sale_id",
            "move_ids",
        ]

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        res._sync_picking_to_sendcloud()
        return res

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("skip_sync_picking_to_sendcloud"):
            if any(item in self._sendcloud_vals_triggering_sync() for item in vals):
                to_sync = self.filtered(lambda p: p.carrier_id.sendcloud_integration_id)
                to_sync._sync_picking_to_sendcloud()
        return res

    def action_cancel(self):
        to_delete_shipments = self.to_delete_sendcloud_pickings()
        res = super().action_cancel()
        self.delete_sendcloud_pickings(to_delete_shipments)
        return res

    def unlink(self):
        to_delete_shipments = self.to_delete_sendcloud_pickings()
        res = super().unlink()
        self.delete_sendcloud_pickings(to_delete_shipments)
        return res

    @api.model
    def _sendcloud_sync_multiple_parcels(self, integration, parcel_vals_list):
        request_data = {"parcels": parcel_vals_list}
        response = integration.create_parcels(request_data)
        if response.get("error"):
            err_msg = response.get("error").get("message")
            raise UserError(_("Sendcloud: %s") % err_msg)
        if response.get("failed_parcels"):
            err_msg = ""
            for failed in response.get("failed_parcels"):
                err_msg += _("%(parcel)s:\n%(errors)s\n\n") % (
                    {
                        "parcel": str(failed.get("parcel")),
                        "errors": str(failed.get("errors")),
                    }
                )
            raise UserError(_("Sendcloud: %s") % err_msg)
        return response["parcels"]

    def _sync_picking_to_sendcloud(self):
        self = self.with_context(skip_sync_picking_to_sendcloud=True)
        pickings = self.filtered(
            lambda p: p.delivery_type == "sendcloud"
            and p.picking_type_code == "outgoing"
            and p.state != "cancel"
            and p.sale_id
        )  # TODo add "or uuid has a value"
        integration_map = defaultdict(list)
        for picking in pickings:
            integration = picking.carrier_id.sendcloud_integration_id
            shipment_vals_list = picking._prepare_sendcloud_parcels_from_picking()
            integration_map[integration] += shipment_vals_list
        err_msg = ""
        for integration in integration_map:
            vals = integration_map[integration]
            err_msg = self._sync_shipment_to_sendcloud(err_msg, integration, vals)
        if err_msg:
            raise UserError(err_msg)
        return pickings

    def _sendcloud_send_shipping(self):
        self.ensure_one()
        res = []
        if self.picking_type_code == "outgoing" and self.sale_id:
            integration = self.carrier_id.sendcloud_integration_id
            vals = self._prepare_sendcloud_parcels_from_picking()
            parcels_data = self._sendcloud_sync_multiple_parcels(integration, vals)
            for parcel in parcels_data:
                # Compute price and tracking number
                price_and_tracking = {
                    "exact_price": self._get_exact_price_of_parcel(parcel),
                    "tracking_number": parcel.get("tracking_number"),
                }
                res.append(price_and_tracking)
            self._sendcloud_create_update_received_parcels(
                parcels_data, integration.company_id.id
            )
        if not res:
            res.append({"exact_price": 0.0, "tracking_number": False})
        return res

    def _sync_shipment_to_sendcloud(self, err_msg, integration, vals):
        _logger.info("Sendcloud create_shipments:%s", integration.sendcloud_code)
        response = integration.with_context(
            sendcloud_ok_response_status=(200, 201)
        ).create_shipments(integration.sendcloud_code, vals)
        for confirmation in response:
            status = confirmation.get("status")

            sendcloud_shipment_uuid = confirmation.get("shipment_uuid")
            if (
                len(self) == 1
                and self.sendcloud_shipment_uuid == sendcloud_shipment_uuid
            ):
                picking = self
            else:
                picking = self.search(
                    [("sendcloud_shipment_uuid", "=", sendcloud_shipment_uuid)], limit=1
                )
            if not picking:
                external_shipment_id = confirmation.get("external_shipment_id")
                if not external_shipment_id:
                    raise  # TODO
                if (
                    len(self) == 1
                    and self.sendcloud_shipment_uuid == sendcloud_shipment_uuid
                ):
                    picking = self
                else:
                    picking = self.env["stock.picking"].search(
                        [("sendcloud_shipment_code", "=", external_shipment_id)]
                    )
                    if len(picking) != 1:
                        raise  # TODO

            if status == "created":
                picking.sendcloud_shipment_uuid = sendcloud_shipment_uuid
                picking.sendcloud_last_cached = fields.Datetime.now()
            elif status == "updated":
                if not picking.sendcloud_shipment_uuid:
                    picking.sendcloud_shipment_uuid = sendcloud_shipment_uuid
                picking.sendcloud_last_cached = fields.Datetime.now()
            elif status == "error":
                error = confirmation.get("error")
                _logger.info(
                    "Sendcloud order %s shipments %s error:%s\n"
                    "picking id: %s\n"
                    "Sent payload: %s",
                    error.get("external_order_id"),
                    error.get("external_shipment_id"),
                    str(error),
                    str(picking.id),
                    str(vals),
                )
                err_msg += _(
                    "Order %(external_order_id)s (shipment %"
                    "(external_shipment_id)s) returned an error:\n"
                ) % (
                    {
                        "external_order_id": error.get("external_order_id"),
                        "external_shipment_id": error.get("external_shipment_id"),
                    }
                )
                err_msg += str(error) + "\n\n"
        return err_msg

    def _get_exact_price_of_parcel(self, parcel):
        pick, _ = parcel["external_reference"].rsplit(",", 1)
        picking = self.filtered(lambda p: p.name == pick)
        country = picking.partner_id.country_id
        carrier = picking.sale_id.carrier_id
        if carrier and country:
            price, _ = carrier._sendcloud_get_price_per_country(country.code)
            return price
        return 0.0

    def _sendcloud_create_update_received_parcels(self, parcels_data, company_id=False):
        self.ensure_one()

        # Existing records
        existing_records = self.sendcloud_parcel_ids

        # Existing records map (internal code -> existing record)
        existing_records_map = {}
        for existing in existing_records:
            if existing.sendcloud_code not in existing_records_map:
                existing_records_map[existing.sendcloud_code] = existing
            else:
                # TODO raise error?
                pass
        # Create/update Odoo parcels
        res = self.env["sendcloud.parcel"]
        odoo_parcels_vals = []
        for parcel in parcels_data:
            # Prepare parcel vals list
            parcels_vals = self.env[
                "sendcloud.parcel"
            ]._prepare_sendcloud_parcel_from_response(parcel)

            if parcel.get("id") in existing_records_map:
                existing_parcel = existing_records_map[parcel.get("id")]
                res |= existing_parcel
                existing_parcel.write(parcels_vals)
            else:
                parcels_vals["company_id"] = company_id or self.env.company.id
                parcels_vals["picking_id"] = self.id
                odoo_parcels_vals += [parcels_vals]
        res += self.env["sendcloud.parcel"].create(odoo_parcels_vals)
        res.action_get_return_portal_url()
        return res

    def button_to_sendcloud_sync(self):
        self.ensure_one()
        if self.carrier_id.delivery_type != "sendcloud":
            return
        self._sync_picking_to_sendcloud()

    # ----------- #
    # Constraints #
    # ----------- #

    @api.constrains("state", "carrier_id", "sendcloud_service_point_address")
    def _constrains_sendcloud_service_point_required(self):
        for record in self.filtered(
            lambda r: r.delivery_type == "sendcloud"
            and r.picking_type_code == "outgoing"
            and not r.carrier_id.sendcloud_is_return
            and r.state == "done"
        ):
            carrier = record.carrier_id
            if carrier.sendcloud_service_point_input == "required":
                if not record.sendcloud_service_point_address:
                    raise ValidationError(_("Sendcloud Service Point is required."))

                if (
                    carrier.sendcloud_integration_id
                    and not carrier.sendcloud_integration_id.service_point_enabled
                ):
                    raise ValidationError(
                        _("Sendcloud Service Point not enabled for this integration.")
                    )

                carrier_names = carrier.sendcloud_integration_id.service_point_carriers
                current_carrier = carrier.sendcloud_carrier
                if (
                    not current_carrier
                    or current_carrier not in safe_eval(carrier_names)
                    or []
                ):
                    raise ValidationError(
                        _("Sendcloud Carrier not enabled for this integration.")
                    )
