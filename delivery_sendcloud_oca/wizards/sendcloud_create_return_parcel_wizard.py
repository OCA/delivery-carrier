# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class SendcloudCreateReturnParcelWizardReturnLocation(models.TransientModel):
    _name = "sendcloud.create.return.parcel.wizard.return.location"
    _description = "Sendcloud Create Return Parcel Wizard Return Location"

    name = fields.Char()
    code = fields.Integer(required=True)
    country_name = fields.Char()
    company_name = fields.Char()
    address_1 = fields.Char()
    address_2 = fields.Char()
    house_number = fields.Char()
    city = fields.Char()
    postal_code = fields.Char()
    senderaddress_labels = fields.Text(default="[]")
    wizard_id = fields.Many2one("sendcloud.create.return.parcel.wizard")


class SendcloudCreateReturnParcelWizardDeliveryOption(models.TransientModel):
    _name = "sendcloud.create.return.parcel.wizard.delivery.option"
    _description = "Sendcloud Create Return Parcel Wizard Delivery Option"

    code = fields.Selection(
        [
            ("drop_off_point", "Drop-off Point"),
            ("in_store", "In Store"),
            ("drop_off_labelless", "Labelless Drop Off"),
        ],
        required=True,
    )
    name = fields.Char(compute="_compute_name", store=True)
    wizard_id = fields.Many2one("sendcloud.create.return.parcel.wizard")

    @api.depends("code")
    def _compute_name(self):
        display_name_map = {
            "drop_off_point": _("Drop-off Point"),
            "in_store": _("In Store"),
            "drop_off_labelless": _("Labelless Drop Off"),
        }
        for wizard in self:
            wizard.name = display_name_map[wizard.code]


class SendcloudCreateReturnParcelWizardRefundOption(models.TransientModel):
    _name = "sendcloud.create.return.parcel.wizard.refund.option"
    _description = "Sendcloud Create Return Parcel Wizard Refund Option"

    name = fields.Char(required=True)
    code = fields.Selection(
        [("money", "Money"), ("credit", "Credit"), ("exchange", "Exchange")],
        string="Refund Type",
    )
    require_message = fields.Boolean()
    wizard_id = fields.Many2one("sendcloud.create.return.parcel.wizard")


class SendcloudCreateReturnParcelWizardReason(models.TransientModel):
    _name = "sendcloud.create.return.parcel.wizard.reason"
    _description = "Sendcloud Create Return Parcel Wizard Reason"

    name = fields.Char(required=True)
    code = fields.Integer(required=True)
    wizard_id = fields.Many2one("sendcloud.create.return.parcel.wizard")


class SendcloudCreateReturnParcelWizardLine(models.TransientModel):
    _name = "sendcloud.create.return.parcel.wizard.line"
    _description = "Sendcloud Create Return Parcel Wizard Line"

    name = fields.Char()
    sendcloud_code = fields.Char(required=True)
    quantity = fields.Integer(required=True)
    price = fields.Float()
    return_reason = fields.Integer(
        default=3
    )  # TODO: Use this field to override wizard value
    return_message = fields.Text()  # TODO: Use this field to override wizard value
    wizard_id = fields.Many2one("sendcloud.create.return.parcel.wizard")


class SendcloudCreateReturnParcelWizard(models.TransientModel):
    _name = "sendcloud.create.return.parcel.wizard"
    _description = "Sendcloud Create Return Parcel Wizard"

    @api.model
    def _default_language(self):
        lang_code = (self.env.lang or "en_US")[0:2].lower()
        lng_map = {
            "en": "en-us",
            "de": "de",
            "es": "es",
            "fr": "fr",
            "it": "it",
            "nl": "nl",
        }
        return lng_map.get(lang_code) or "en-us"

    @api.model
    def _get_languages(self):
        return [
            ("en-us", "English"),
            ("de", "German"),
            ("es", "Spanish"),
            ("fr", "French"),
            ("it", "Italian"),
            ("nl", "Dutch"),
        ]

    # Parameters
    postal_code = fields.Char(required=True)
    identifier = fields.Char(required=True)
    parcel_id = fields.Many2one("sendcloud.parcel")
    brand_id = fields.Many2one("sendcloud.brand", required=True)
    language = fields.Selection(
        selection=lambda self: self._get_languages(),
        default=lambda self: self._default_language(),
        required=True,
    )

    # Tokens
    service_points_token = fields.Text(readonly=True)
    access_token = fields.Text(readonly=True)

    poller_url = fields.Char(readonly=True)
    shop_distances = fields.Text(readonly=True)
    national_carrier_contact = fields.Text(readonly=True)
    service_point = fields.Text(readonly=True)

    # Error feedback
    error_message = fields.Text(readonly=True)
    info_message = fields.Text(readonly=True)

    # Lines
    line_ids = fields.One2many(
        "sendcloud.create.return.parcel.wizard.line", "wizard_id", "Lines"
    )

    # Refund options
    refund_options = fields.Text(default="[]", string="Refund Options Cached")
    refund_option_ids = fields.One2many(
        "sendcloud.create.return.parcel.wizard.refund.option",
        "wizard_id",
        "Refund Options",
    )
    refund_option_id = fields.Many2one(
        "sendcloud.create.return.parcel.wizard.refund.option",
        domain="[('id', 'in', refund_option_ids)]",
    )
    refund_message = fields.Text()
    refund_option_require_message = fields.Boolean(
        related="refund_option_id.require_message"
    )

    # Return location
    return_locations = fields.Text(default="[]", string="Return Locations Cached")
    return_location_ids = fields.One2many(
        "sendcloud.create.return.parcel.wizard.return.location",
        "wizard_id",
        "Return Locations",
    )
    return_location_id = fields.Many2one(
        "sendcloud.create.return.parcel.wizard.return.location",
        domain="[('id', 'in', return_location_ids)]",
    )

    # Reasons
    reasons = fields.Text(default="[]", string="Reasons Cached")
    reason_ids = fields.One2many(
        "sendcloud.create.return.parcel.wizard.reason", "wizard_id", "Reasons"
    )
    reason_id = fields.Many2one(
        "sendcloud.create.return.parcel.wizard.reason",
        domain="[('id', 'in', reason_ids)]",
    )
    reason_message = fields.Text()

    # Delivery Options
    delivery_options = fields.Text(default="[]", string="Delivery Options Cached")
    delivery_option_ids = fields.One2many(
        "sendcloud.create.return.parcel.wizard.delivery.option",
        "wizard_id",
        "Delivery Options",
    )
    delivery_option_id = fields.Many2one(
        "sendcloud.create.return.parcel.wizard.delivery.option",
        domain="[('id', 'in', delivery_option_ids)]",
    )

    collo_count = fields.Integer()

    # Portal settings lookup
    support_url = fields.Char()
    return_policy_url = fields.Char()
    enable_refunds = fields.Boolean()
    return_fee = fields.Float()
    return_portal_url = fields.Char()

    @api.onchange("brand_id", "parcel_id", "postal_code", "identifier")
    def _onchange_configuration(self):
        self.error_message = False
        self.info_message = False

    @api.model
    def _prepare_sendcloud_return_location_from_response(self, records_data):
        return {
            "code": records_data.get("id"),
            "name": "[{id}] {company_name} - {country_name}".format(
                id=records_data.get("id"),
                company_name=records_data.get("company_name"),
                country_name=records_data.get("country_name"),
            ),
            "country_name": records_data.get("country_name"),
            "company_name": records_data.get("company_name"),
            "address_1": records_data.get("address_1"),
            "address_2": records_data.get("address_2"),
            "house_number": records_data.get("house_number"),
            "city": records_data.get("city"),
            "postal_code": records_data.get("postal_code"),
            "senderaddress_labels": records_data.get("senderaddress_labels"),
        }

    def _get_return_portal_settings(self, integration):
        self.ensure_one()
        response = integration.get_return_portal_settings(
            self.brand_id.domain, self.language
        )
        if response.get("error"):
            error_msg = response.get("error", {}).get("message", "")
            error_code = response.get("error", {}).get("code", "")
            raise UserError(
                _("Sendcloud: error %(error_code)s\n%(error_msg)s")
                % ({"error_code": error_code, "error_msg": error_msg})
            )
        portal = response.get("portal")
        return_portal_url = "https://%s.shipping-portal.com/rp/" % portal.get("domain")
        self.reasons = portal.get("reasons")
        self.support_url = portal.get("support_url")
        self.return_policy_url = portal.get("return_policy_url")
        self.enable_refunds = portal.get("enable_refunds")
        self.refund_options = portal.get("refund_options")
        self.return_fee = portal.get("return_fee")
        self.delivery_options = portal.get("delivery_options")
        self.return_locations = response.get("return_locations")
        self.return_portal_url = return_portal_url
        brand_data = portal.get("brand")
        if brand_data:
            self.env["sendcloud.brand"].sendcloud_update_brands(
                [brand_data], self.brand_id.company_id
            )

    def button_confirm(self):
        self.ensure_one()
        self.error_message = False
        self.info_message = False

        integration = self.brand_id.company_id.sendcloud_default_integration_id
        self._get_return_portal_settings(integration)
        if (
            not self.parcel_id
            and self.env.context.get("active_model") == "sendcloud.parcel"
        ):
            parcel = self.env["sendcloud.parcel"].browse(self.env.context["active_id"])
            self.parcel_id = parcel
        if not self.access_token:
            self._step1(integration)

            return {
                "name": _("Create Return Parcel"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "sendcloud.create.return.parcel.wizard",
                "res_id": self.id,
                "target": "new",
            }
        else:
            sendcloud_return = self._step2(integration)
        return {
            "name": _("Return Details"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sendcloud.return",
            "type": "ir.actions.act_window",
            "target": "current",
            "res_id": sendcloud_return.id,
        }

    def _step1(self, integration):
        params = {"postal_code": self.postal_code, "identifier": self.identifier}
        outgoing_parcel_data = integration.get_return_portal_outgoing_parcel(
            self.brand_id.domain, params
        )
        if outgoing_parcel_data.get("error"):
            res_error = outgoing_parcel_data.get("error")
            err_msg = _("Sendcloud: %(message)s (error code: '%(code)s')") % (
                {"message": res_error.get("message"), "code": res_error.get("code")}
            )
            self.error_message = "%s\n" % err_msg
        else:
            self.service_points_token = outgoing_parcel_data.get("service_points_token")
            self.access_token = outgoing_parcel_data.get("access_token")

            service_point = outgoing_parcel_data.get("data", {}).get("service_point")
            self.service_point = json.dumps(service_point)
            self.shop_distances = str(
                outgoing_parcel_data.get("data", {}).get("shop_distances")
            )
            self.national_carrier_contact = str(
                outgoing_parcel_data.get("data", {}).get("national_carrier_contact")
            )

            # Parcel
            parcel_data = outgoing_parcel_data.get("data", {}).get("parcel")
            parcels = self.env["sendcloud.parcel"].sendcloud_create_update_parcels(
                [parcel_data], self.brand_id.company_id.id
            )
            self.parcel_id = fields.first(parcels)

            # Carriers
            carriers_data = outgoing_parcel_data.get("data", {}).get("carriers")
            self.sendcloud_update_carriers(carriers_data)

            # Lines
            product_vals = []
            for product_data in outgoing_parcel_data.get("data", {}).get("products"):
                product_vals.append(
                    {
                        "sendcloud_code": product_data.get("id"),
                        "name": product_data.get("name"),
                        "price": float(product_data.get("price")),
                        "quantity": product_data.get("quantity"),
                        "wizard_id": self.id,
                    }
                )
            self.env["sendcloud.create.return.parcel.wizard.line"].create(product_vals)

            # Refund Options
            option_vals = []
            for option_data in safe_eval(self.refund_options or "[]"):
                option_vals.append(
                    {
                        "code": option_data.get("code"),
                        "name": option_data.get("label"),
                        "require_message": option_data.get("require_message"),
                        "wizard_id": self.id,
                    }
                )
            self.env["sendcloud.create.return.parcel.wizard.refund.option"].create(
                option_vals
            )

            # Reasons
            reason_vals = []
            for reason_data in safe_eval(self.reasons or "[]"):
                reason_vals.append(
                    {
                        "code": reason_data.get("id"),
                        "name": reason_data.get("description"),
                        "wizard_id": self.id,
                    }
                )
            self.env["sendcloud.create.return.parcel.wizard.reason"].create(reason_vals)

            # Return Locations
            return_location_vals = []
            for return_location_data in safe_eval(self.return_locations or "[]"):
                vals = self._prepare_sendcloud_return_location_from_response(
                    return_location_data
                )
                vals["wizard_id"] = self.id
                return_location_vals.append(vals)
            self.env["sendcloud.create.return.parcel.wizard.return.location"].create(
                return_location_vals
            )

            # Delivery Options
            delivery_option_vals = []
            for option_data in safe_eval(self.delivery_options or "[]"):
                vals = self._prepare_sendcloud_delivery_option_from_response(
                    option_data
                )
                vals["wizard_id"] = self.id
                delivery_option_vals.append(vals)
            self.env["sendcloud.create.return.parcel.wizard.delivery.option"].create(
                delivery_option_vals
            )

    def _prepare_sendcloud_delivery_option_from_response(self, delivery_option_data):
        return {"code": delivery_option_data}

    def _step2(self, integration):
        headers = {"Authorization": "Bearer " + self.access_token}
        payload = {"outgoing_parcel": self.parcel_id.sendcloud_code}
        products = []
        for line in self.line_ids:
            product_vals = {
                "product_id": str(line.sendcloud_code),  # TODO is it correct?
                "quantity": line.quantity,
                "description": line.name,
                "value": str(line.price),
            }
            if self.reason_id:
                product_vals["return_reason"] = self.reason_id.code
            if self.reason_message:
                product_vals["return_message"] = self.reason_message
            products.append(product_vals)
        payload.update({"products": products})
        payload.update(
            {
                "incoming_parcel": {
                    "collo_count": self.collo_count,
                    "from_address_1": self.parcel_id.address,
                    "from_address_2": self.parcel_id.address_2 or "",
                    "from_city": self.parcel_id.city,
                    "from_company_name": self.parcel_id.company_name,
                    "from_country": self.parcel_id.country_iso_2,
                    "from_email": self.parcel_id.email,
                    "from_house_number": self.parcel_id.house_number,
                    "from_name": self.parcel_id.partner_name,
                    "from_postal_code": self.parcel_id.postal_code,
                    "from_telephone": self.parcel_id.telephone,
                }
            }
        )
        if not self.refund_option_id:
            raise UserError(_("Refund option is required"))
        if self.refund_option_require_message and not self.refund_message:
            raise UserError(_("Refund message is required"))
        refund_option_code = self.refund_option_id.code
        refund_message = self.refund_message or ""
        refund_data = {
            "refund": {
                "refund_type": {"code": refund_option_code},
                "message": refund_message,
            }
        }
        payload.update(refund_data)
        if self.line_ids:
            # The ID of the chosen return reason.
            # Only needed if items are not provided, else defaults to null.
            reason = None
        else:
            if not self.reason_id:
                raise UserError(_("Reason is required"))
            reason = self.reason_id.code
        payload.update({"reason": reason})
        payload.update(
            {
                "delivery_option": self.delivery_option_id.code,
                "service_point": json.loads(self.service_point or "{}"),
                "message": "",  # TODO
            }
        )
        response = integration.create_return_portal_incoming_parcel(
            self.brand_id.domain, payload, headers
        )
        # Create sendcloud return
        return_code = response.get("return")
        sendcloud_return_data = integration.get_return(return_code)
        sendcloud_return = self.env[
            "sendcloud.return"
        ].sendcloud_create_or_update_returns(
            sendcloud_return_data, self.brand_id.company_id
        )
        # Create sendcloud incoming parcels
        incoming_parcels = response.get("incoming_parcels")
        odoo_parcels_vals = []
        for incoming_parcel_code in incoming_parcels:
            parcel = integration.get_parcel(incoming_parcel_code)
            parcels_vals = self.env[
                "sendcloud.parcel"
            ]._prepare_sendcloud_parcel_from_response(parcel)
            parcels_vals["picking_id"] = self.parcel_id.picking_id.id
            parcels_vals["company_id"] = self.env.company.id
        odoo_parcels_vals += [parcels_vals]
        self.env["sendcloud.parcel"].create(odoo_parcels_vals)
        # Manage Odoo return
        # Label creation poller
        self.poller_url = response.get("poller_url")
        # TODO manage Label download. This endpoint returns a PDF.
        # {
        #     "tracking_numbers": ["3SYZXG109696559"],
        #     "return": 346721,
        #     "download_url": "https://panel.sendcloud.sc/api/v2/brand/andrea1/return-portal/label/download?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzQ2NzIxfQ.Z10kyEhX8ljzTXvNwxOsfWltwStOeQAFWeTp8akQgr4",
        #     "parcels": [49442788]
        # }
        return sendcloud_return

    @api.onchange("parcel_id")
    def onchange_parcel_id(self):
        self.postal_code = (
            self.parcel_id.postal_code or self.parcel_id.picking_id.partner_id.zip
        )
        self.identifier = self.parcel_id.tracking_number

    @api.model
    def sendcloud_update_carriers(self, carriers_data):
        retrieved_carriers = [carrier.get("code") for carrier in carriers_data]
        self.env["sendcloud.carrier"]._create_update_carriers(retrieved_carriers)
