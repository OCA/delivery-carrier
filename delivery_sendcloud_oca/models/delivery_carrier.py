# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_round
from odoo.tools.safe_eval import safe_eval


class DeliveryCarrier(models.Model):
    _name = "delivery.carrier"
    _inherit = ["delivery.carrier", "sendcloud.mixin"]

    delivery_type = fields.Selection(
        selection_add=[("sendcloud", "Sendcloud")],
        ondelete={
            "sendcloud": lambda recs: recs.write(
                {
                    "delivery_type": "fixed",
                    "fixed_price": 0,
                }
            )
        },
    )

    sendcloud_code = fields.Integer()
    sendcloud_carrier = fields.Char()
    sendcloud_service_point_input = fields.Selection(
        [("none", "None"), ("required", "Required")], default="none"
    )
    sendcloud_min_weight = fields.Float()
    sendcloud_max_weight = fields.Float()
    sendcloud_price = fields.Float(
        help="When this value is null, the price is calculated based on the"
        " pricelist by countries"
    )
    sendcloud_is_return = fields.Boolean()
    sendcloud_country_ids = fields.One2many(
        "sendcloud.shipping.method.country",
        compute="_compute_sendcloud_country_ids",
        string="Price per Country",
    )
    sendcloud_service_point_required = fields.Boolean(
        compute="_compute_sendcloud_service_point_required"
    )
    sendcloud_sender_address_id = fields.Many2one("sendcloud.sender.address")

    sendcloud_integration_id = fields.Many2one(
        "sendcloud.integration", compute="_compute_sendcloud_integration_id"
    )
    sendcloud_sync_countries = fields.Boolean(
        string="Synchronize countries with Sendcloud", default=True
    )

    # -------- #
    # Computed #
    # -------- #

    @api.depends("company_id")
    def _compute_sendcloud_integration_id(self):
        for carrier in self:
            carrier.sendcloud_integration_id = (
                carrier.company_id.sendcloud_default_integration_id
            )

    @api.depends("sendcloud_service_point_input", "delivery_type")
    def _compute_sendcloud_service_point_required(self):
        sendcloud_service_point_required_carriers = self.filtered(
            lambda c: c.delivery_type == "sendcloud"
            and c.sendcloud_service_point_input == "required"
        )
        sendcloud_service_point_required_carriers.update(
            {"sendcloud_service_point_required": True}
        )
        (self - sendcloud_service_point_required_carriers).update(
            {"sendcloud_service_point_required": False}
        )

    def _compute_sendcloud_country_ids(self):
        countries = self.env["sendcloud.shipping.method.country"].search([])
        for carrier in self:
            carrier.sendcloud_country_ids = countries.filtered(
                lambda country, current_carrier=carrier: country.company_id
                == current_carrier.company_id
                and country.method_code == current_carrier.sendcloud_code
            )

    # -------------------------- #
    # API for Sendcloud provider #
    # -------------------------- #

    def sendcloud_rate_shipment(self, order):
        self.ensure_one()
        res = {
            "success": False,
            "price": 0.0,
            "warning_message": False,
            "error_message": False,
        }
        if not order.partner_shipping_id.country_id:
            res["error_message"] = _("Partner does not have any country.")
            return res

        country = order.partner_shipping_id.country_id
        price, method_country = self._sendcloud_get_price_per_country(country.code)
        price_digits = self.env["decimal.precision"].precision_get("Product Price")
        price = float_round(price, precision_digits=price_digits)
        price = order._sendcloud_convert_price_in_euro(price)
        res["success"] = True
        res["price"] = price
        res["sendcloud_country_specific_product"] = method_country.product_id

        if self.sendcloud_service_point_input == "required":
            res["warning_message"] = _("This shipping method requires a Service Point.")

        return res

    def sendcloud_send_shipping(self, pickings):
        self.ensure_one()
        # Dispatch Order and create labels
        res = pickings._sendcloud_send_shipping()
        parcels = pickings.mapped("sendcloud_parcel_ids")
        parcels._generate_parcel_labels()
        return res

    def sendcloud_cancel_shipment(self, picking):
        ctx = {"skip_sync_picking_to_sendcloud": True, "skip_cancel_parcel": True}
        deleted_parcels = []
        for parcel_code in picking.mapped("sendcloud_parcel_ids.sendcloud_code"):
            integration = picking.company_id.sendcloud_default_integration_id
            res = integration.cancel_parcel(parcel_code)
            if res.get("status") == "deleted":
                deleted_parcels.append(parcel_code)
            elif (
                res.get("status") == "failed"
                and res.get("message") == "This shipment is already being cancelled."
            ):
                deleted_parcels.append(parcel_code)
            elif res.get("error", {}).get("code") == 404:
                deleted_parcels.append(parcel_code)  # ignore "Not Found" error
            elif res.get("error"):
                raise ValidationError(
                    _("Sendcloud: %(error_message)s")
                    % {"error_message": res["error"].get("message")}
                )
        parcels_to_delete = picking.sendcloud_parcel_ids.filtered(
            lambda p: p.sendcloud_code in deleted_parcels
        )
        parcels_to_delete.with_context(**ctx).unlink()
        picking.with_context(**ctx).write({"carrier_price": 0.0})

    # ------------------------------- #
    # Inherits for Sendcloud provider #
    # ------------------------------- #

    def _compute_can_generate_return(self):
        res = super()._compute_can_generate_return()
        self.filtered(lambda c: c.delivery_type == "sendcloud").update(
            {"can_generate_return": True}
        )
        return res

    def available_carriers(self, partner):
        """
        Standard Odoo method, invoked by the super(), already filters shipping
        methods, including Sendcloud shipping methods, by the country of the
        selected partner.
        In addition, this method filters the Sendcloud shipping methods by
         - sender address (warehouse address)
         - weight range
         - enabled/disabled service point in Sendcloud integration.
        :param partner:
        :return:
        """
        res = super().available_carriers(partner)

        sendcloud_carriers = res.filtered(
            lambda c: c.delivery_type == "sendcloud" and c.sendcloud_is_return is False
        )
        other_carriers = res.filtered(lambda c: c.delivery_type != "sendcloud")
        if sendcloud_carriers:
            # Retrieve current sale order
            order_id = self.env.context.get("sale_order_id")
            if not order_id:
                order_id = self.env.context.get("default_order_id")
            if (
                not order_id
                and self.env.context.get("active_model") == "choose.delivery.carrier"
            ):
                wizard = self.env["choose.delivery.carrier"].browse(
                    self.env.context.get("active_id")
                )
                order_id = wizard.order_id.id
            if not order_id:
                return other_carriers
            order = self.env["sale.order"].browse(order_id)
            # get sender address (warehouse)
            warehouse = order.warehouse_id
            if not warehouse.sencloud_sender_address_id:
                # use standard server address
                sender_address = self._get_default_sender_address_per_company(
                    warehouse.company_id.id
                )
            else:
                sender_address = warehouse.sencloud_sender_address_id

            # filter by weight
            # TODO are there sendcloud shipping methods without weight limit?
            weight = order.sendcloud_order_weight
            sendcloud_carriers = sendcloud_carriers.filtered(
                lambda c: c.sendcloud_min_weight <= weight <= c.sendcloud_max_weight
            )

            # filter by sender address (warehouse) and delivery address (partner)
            countries = self.env["sendcloud.shipping.method.country"].search(
                [
                    ("company_id", "=", order.company_id.id),
                    ("from_iso_2", "=", sender_address.country),
                    ("iso_2", "=", partner.country_id.code),
                ]
            )
            method_codes = countries.mapped("method_code")
            sendcloud_carriers = sendcloud_carriers.filtered(
                lambda c: c.sendcloud_code in method_codes
            )

            # filter out carriers requiring service points that are not enabled
            without_service_point = sendcloud_carriers.filtered(
                lambda c: c.sendcloud_service_point_input != "required"
            )
            with_service_point = sendcloud_carriers.filtered(
                lambda c: c.sendcloud_service_point_input == "required"
                and c.sendcloud_integration_id.service_point_enabled
            )
            enabled_service_point = self.env["delivery.carrier"]
            for carrier in with_service_point:
                carrier_names = carrier.sendcloud_integration_id.service_point_carriers
                current_carrier = carrier.sendcloud_carrier
                if (
                    current_carrier
                    and current_carrier in safe_eval(carrier_names)
                    or []
                ):
                    enabled_service_point += carrier
            sendcloud_carriers = without_service_point + enabled_service_point

        return (sendcloud_carriers + other_carriers).sorted(
            key=lambda carrier: carrier.name
        )

    # ----------------- #
    # Sendcloud methods #
    # ----------------- #

    def _sendcloud_set_countries(self):
        for record in self.filtered(
            lambda r: r.delivery_type == "sendcloud" and r.sendcloud_sync_countries
        ):
            record.country_ids = record._sendcloud_get_countries()

    def _sendcloud_get_countries(self):
        self.ensure_one()
        countries = self.env["sendcloud.shipping.method.country"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("method_code", "=", self.sendcloud_code),
            ]
        )
        iso_2_list = countries.mapped("iso_2")
        return self.env["res.country"].search([("code", "in", iso_2_list)])

    def _sendcloud_get_price_per_country(self, country_code):
        self.ensure_one()
        if self.sendcloud_price:
            return self.sendcloud_price
        shipping_method_country = self.env["sendcloud.shipping.method.country"].search(
            [
                ("iso_2", "=", country_code),
                ("company_id", "=", self.company_id.id),
                ("method_code", "=", self.sendcloud_code),
            ],
            limit=1,
        )
        return shipping_method_country.price_custom, shipping_method_country

    @api.model
    def _get_default_sender_address_per_company(self, company_id):
        # TODO is there a way to get the default sender address from sendcloud?
        return self.env["sendcloud.sender.address"].search(
            [("company_id", "=", company_id)], limit=1
        )

    @api.model
    def _prepare_sendcloud_shipping_method_from_response(self, carrier):
        return {
            "name": "Sendcloud " + carrier.get("name"),
            "delivery_type": "sendcloud",
            "sendcloud_code": carrier.get("id"),
            "sendcloud_max_weight": carrier.get("max_weight"),
            "sendcloud_min_weight": carrier.get("min_weight"),
            "sendcloud_carrier": carrier.get("carrier"),
            "sendcloud_service_point_input": carrier.get("service_point_input").lower(),
            "sendcloud_price": carrier.get("price"),
        }

    @api.model
    def _get_sendcloud_product_delivery(self, company_id):
        """This method gets a default delivery product for newly created
        Sendcloud shipping methods.
        :param vals: dict of values to update
        :return: updated dict of values
        """
        product = self.env["product.product"].search(
            [
                ("default_code", "=", "sendcloud_delivery"),
                ("company_id", "in", [company_id, False]),
            ],
            limit=1,
        )
        if product:
            return product
        return self.env["product.product"].create(
            {
                "name": "Sendcloud delivery charges",
                "default_code": "sendcloud_delivery",
                "type": "service",
                "categ_id": self.env.ref("delivery.product_category_deliveries").id,
                "sale_ok": False,
                "purchase_ok": False,
                "list_price": 0.0,
                "description_sale": "Delivery Cost",
                "company_id": company_id,
            }
        )

    @api.model
    def _sendcloud_create_update_shipping_methods(
        self, shipping_methods, company_id, is_return=False
    ):
        """Sync all available shipping methods for a specific company,
         regardless of the sender address.
        :return:
        """

        product = self._get_sendcloud_product_delivery(company_id)

        # All shipping methods
        domain = [
            ("delivery_type", "=", "sendcloud"),
            ("company_id", "=", company_id),
            ("sendcloud_is_return", "=", is_return),
        ]
        all_shipping_methods = self.with_context(active_test=False).search(domain)

        # Existing records
        shipping_methods_list = [method.get("id") for method in shipping_methods]
        existing_shipping_methods = all_shipping_methods.filtered(
            lambda c: c.sendcloud_code in shipping_methods_list
        )

        # Existing shipping methods map (internal code -> existing shipping methods)
        existing_shipping_methods_map = {}
        for existing in existing_shipping_methods:
            if existing.sendcloud_code not in existing_shipping_methods_map:
                existing_shipping_methods_map[existing.sendcloud_code] = self.env[
                    "delivery.carrier"
                ].browse()
            existing_shipping_methods_map[existing.sendcloud_code] |= existing

        # Disabled shipping methods
        disabled_shipping_methods = all_shipping_methods - existing_shipping_methods
        disabled_shipping_methods.write({"active": False})

        # Created shipping methods and related pricelist by countries
        new_shipping_methods_vals = []
        new_country_vals = []
        for method in shipping_methods:
            vals = self._prepare_sendcloud_shipping_method_from_response(method)
            vals["product_id"] = product.id
            vals["sendcloud_is_return"] = is_return
            if method.get("id") in existing_shipping_methods_map:
                vals.pop("name")
                existing_shipping_methods_map[method.get("id")].write(vals)
            else:
                vals["company_id"] = company_id
                new_shipping_methods_vals += [vals]
            for country in method.get("countries"):
                new_country_vals.append(
                    {
                        "sendcloud_code": country.get("id"),
                        "iso_2": country.get("iso_2"),
                        "iso_3": country.get("iso_3"),
                        "from_iso_2": country.get("from_iso_2"),
                        "from_iso_3": country.get("from_iso_3"),
                        "price": country.get("price"),
                        "method_code": method.get("id"),
                        "sendcloud_is_return": is_return,
                        "company_id": company_id,
                    }
                )
        new_created_shipping_methods = self.create(new_shipping_methods_vals)
        self.sudo().env["sendcloud.shipping.method.country"].search(
            [
                ("company_id", "=", company_id),
                ("sendcloud_is_return", "=", is_return),
            ]
        ).unlink()
        self.sudo().env["sendcloud.shipping.method.country"].create(new_country_vals)

        # Updated shipping methods
        updated_shipping_methods = (
            existing_shipping_methods + new_created_shipping_methods
        )
        updated_shipping_methods._sendcloud_set_countries()
        updated_shipping_methods.write({"active": True})

        # Carriers
        self.sendcloud_update_carriers(updated_shipping_methods)
        return shipping_methods

    @api.model
    def sendcloud_update_carriers(self, updated_shipping_methods):
        retrieved_carriers = updated_shipping_methods.mapped("sendcloud_carrier")
        self.env["sendcloud.carrier"]._create_update_carriers(retrieved_carriers)

    @api.model
    def sendcloud_sync_shipping_method(self):
        for company in self.env["res.company"].search([]):
            integration = company.sendcloud_default_integration_id
            if integration:
                params = {"sender_address": "all"}
                shipping_methods = integration.get_shipping_methods(params)
                self._sendcloud_create_update_shipping_methods(
                    shipping_methods, company.id
                )
                params = {"sender_address": "all", "is_return": True}
                shipping_methods = integration.get_shipping_methods(params)
                self._sendcloud_create_update_shipping_methods(
                    shipping_methods, company.id, is_return=True
                )

    def button_from_sendcloud_sync(self):
        self.ensure_one()
        if self.delivery_type != "sendcloud":
            return
        integration = self.company_id.sendcloud_default_integration_id
        if integration:
            self._update_sendcloud_delivery_carrier(integration)

    def _update_sendcloud_delivery_carrier(self, integration):
        self.ensure_one()
        internal_code = self.sendcloud_code
        params = {"sender_address": "all"}
        carrier = integration.get_shipping_method(internal_code, params)
        vals = self._prepare_sendcloud_shipping_method_from_response(carrier)
        vals.pop("name")
        self.write(vals)

    def write(self, vals):
        res = super().write(vals)
        if "delivery_type" in vals:
            self._sendcloud_set_countries()
        return res

    # ----------- #
    # Constraints #
    # ----------- #

    @api.constrains("delivery_type", "company_id")
    def _constrains_sendcloud_integration_company_id(self):
        for record in self.filtered(lambda r: r.delivery_type == "sendcloud"):
            if not record.company_id:
                raise ValidationError(
                    _("The company is mandatory when delivery carrier is Sendcloud.")
                )
            if record.sendcloud_integration_id.company_id != record.company_id:
                raise ValidationError(
                    _("The company is not consistent with the integration company.")
                )
