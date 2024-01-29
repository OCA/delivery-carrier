# Copyright 2022 FactorLibre - Jorge Martínez <jorge.martinez@factorlibre.com>
# Copyright 2022 FactorLibre - Zahra Velasco <zahra.velasco@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, config, ustr

from .deliverea_request import DelivereaRequest

_logger = logging.getLogger(__name__)


MANDATORY_SENDER_FIELDS = (
    "name",
    "address",
    "city",
    "zipCode",
    "countryCode",
    "phone",
    "email",
)
MANDATORY_PAYLOAD_FIELDS = (
    "carrierCode",
    "serviceCode",
    "distributionCenterId",
    "clientReference",
)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    @api.model
    def _get_default_field(self):
        default_field = self.env["ir.model.fields"].search(
            [
                ("model_id.name", "=", "stock.picking"),
                ("name", "=", "note"),
            ]
        )
        return default_field.id

    delivery_type = fields.Selection(
        selection_add=[("deliverea", "Deliverea")],
        ondelete={"deliverea": "set default"},
    )
    deliverea_username = fields.Char()
    deliverea_password = fields.Char()
    deliverea_distribution_center_id = fields.Many2one(
        comodel_name="deliverea.distribution.center",
        string="Deliverea Distribution Center",
    )
    deliverea_url_prod = fields.Char(string="Deliverea production environment URL")
    deliverea_url_test = fields.Char(string="Deliverea test environment URL")
    deliverea_url_tracking = fields.Char(string="Deliverea tracking URL")
    deliverea_description = fields.Char(
        string="Deliverea Articles Description",
        help="Description of the expedition articles (required for crossborder"
        " international expeditions if no description by parcel[items] is present)",
    )
    deliverea_note_selection_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Select Note Field",
        domain="[('model_id', '=', 'stock.picking')]",
        default=_get_default_field,
        help="It allows to choose the field that we want "
        "to show within the carrier observations",
    )
    deliverea_default_packaging_id = fields.Many2one(
        comodel_name="stock.package.type",
        string="Default Packaging Type",
        domain=[("package_carrier_type", "=", "deliverea")],
        help="Default weight, height, width and length for packages",
    )
    deliverea_notifications_sms = fields.Boolean(
        string="Notify by sms",
        help="The carrier will send info sms(s) to the final customer",
    )
    deliverea_notifications_email = fields.Boolean(
        string="Notify by email",
        help="The carrier will send info email(s) to the final customer",
    )
    deliverea_saturday_delivery = fields.Boolean(
        string="Saturday Delivery",
        help="Whether or not the expedition should be delivered on Saturday"
        " or wait until next Monday (availability depends on carrier and service)",
    )
    deliverea_return_label = fields.Boolean(
        string="Return Label",
        help="Whether or not to include dormant return label in case the final customer"
        " wants to return the expedition (availability depends on carrier and service)",
    )
    deliverea_return_proof_delivery = fields.Boolean(
        string="Return Proof Delivery",
        help="Whether or not to a proof of delivery should be returned"
        " back to origin (availability depends on carrier and service)",
    )
    deliverea_hide_sender = fields.Boolean(
        string="Hide Sender",
        help="Whether or not to hide sender information in the printed label"
        " (availability depends on carrier and service)",
    )
    deliverea_carrier_service_id = fields.Many2one(
        comodel_name="carrier.deliverea.service",
        domain="[('deliverea_distribution_center_id', '=', deliverea_distribution_center_id)]",
    )

    def deliverea_get_distribution_centers(self):
        deliverea_request = DelivereaRequest(self)
        deliverea_distribution_center_env = self.env["deliverea.distribution.center"]
        distribution_centers = deliverea_request.get_distribution_centers()
        for distribution_center in distribution_centers.get("data"):
            center = deliverea_distribution_center_env.search(
                [("uuid", "=", distribution_center.get("id"))]
            )
            vals = {
                "active": distribution_center.get("active"),
                "name": distribution_center.get("name"),
                "address": distribution_center.get("address"),
                "city": distribution_center.get("city"),
                "zip": distribution_center.get("zipCode"),
                "observations": distribution_center.get("observations"),
                "phone": distribution_center.get("phone"),
                "email": distribution_center.get("email"),
                "latitude": distribution_center.get("latitude"),
                "longitude": distribution_center.get("longitude"),
                "billing_account": distribution_center.get("billingAccountId"),
            }
            if not center:
                country_id = self.env["res.country"].search(
                    [("code", "=", distribution_center.get("countryCode"))]
                )
                deliverea_distribution_center_env.create(
                    {
                        "uuid": distribution_center.get("id"),
                        "country_id": country_id.id if country_id else False,
                        **vals,
                    }
                )
            else:
                center.write(vals)

    def deliverea_get_services_cron(self, extra_domain=None):
        domain = [
            ("delivery_type", "=", "deliverea"),
            ("deliverea_distribution_center_id", "!=", False),
        ]
        if extra_domain:
            domain.extend(extra_domain)
        delivery_carrier_ids = self.env["delivery.carrier"].search(domain)
        for delivery_carrier in delivery_carrier_ids:
            try:
                delivery_carrier.deliverea_get_services()
                self.env.cr.savepoint()
                if not config["test_enable"]:
                    _logger.info(
                        'The services of the delivery carrier "%s" has been updated'
                        % delivery_carrier.name
                    )
            except Exception as e:
                _logger.warning(ustr(e))
                self.env.cr.rollback()
        return True

    def deliverea_get_services(self):
        deliverea_request = DelivereaRequest(self)
        if not self.deliverea_distribution_center_id:
            raise UserError(_("You must select a distribution center first"))
        carriers = deliverea_request.get_carrier_list(
            self.deliverea_distribution_center_id.uuid
        )
        for carrier in carriers.get("data"):
            services = deliverea_request.get_carrier_detail(
                distribution_center_id=self.deliverea_distribution_center_id.uuid,
                carrier_code=carrier.get("code"),
                cost_center=carrier.get("costCenters")[0].get("code"),
            )
            for service in services.get("services"):
                service_id = self.env["carrier.deliverea.service"].search(
                    [
                        ("carrier_code", "=", carrier.get("code")),
                        ("code", "=", service.get("code")),
                        ("active", "in", [True, False]),
                    ]
                )
                active_service = service.get("active", False)
                # Si un servicio no esta creado y viene desactivada, no la creamos
                if service_id and service_id.active != active_service:
                    service_id.write({"active": active_service})
                if not active_service and not service_id:
                    continue
                services_parameter = (
                    deliverea_request.get_carrier_services_integrations(
                        carrier.get("code"), services.get("integrationCode")
                    )
                )
                service_parameter = next(
                    (
                        item
                        for item in services_parameter.get("services")
                        if item.get("code") == service.get("code")
                    ),
                    {},
                )
                if not service_id:
                    service_id = self.env["carrier.deliverea.service"].create(
                        {
                            "name": carrier.get("code", "").upper()
                            + " "
                            + (
                                service_parameter.get("name", "")
                                or service.get("code", "")
                            ),
                            "code": service.get("code"),
                            "description": service_parameter.get("description") or "",
                            "carrier_code": carrier.get("code"),
                            "deliverea_distribution_center_id": (
                                self.deliverea_distribution_center_id.id
                            ),
                            "active": active_service,
                        }
                    )
                for parameter in service_parameter.get("parameters", []):
                    parameter_id = self.env["carrier.deliverea.parameter"].search(
                        [
                            ("name", "=", parameter.get("name")),
                            ("type", "=", parameter.get("necessity").get("type")),
                        ]
                    )
                    if not parameter_id:
                        parameter_id = self.env["carrier.deliverea.parameter"].create(
                            {
                                "name": parameter.get("name"),
                                "type": parameter.get("necessity").get("type"),
                            }
                        )
                    if parameter_id.id not in service_id.deliverea_parameters.ids:
                        service_id.deliverea_parameters = [
                            (
                                4,
                                parameter_id.id,
                            )
                        ]

    def _delete_empty_values(self, values):
        delete = []
        for key, value in values.items():
            if values[key].__class__ is dict:
                self._delete_empty_values(values[key])
            if value == "":
                delete.append(key)
        for key in delete:
            del values[key]

    def _check_mandatory_fields(self, values, mandatory_list, object_id):
        errors = []
        for key, value in values.items():
            if key in mandatory_list and not value:
                errors.append(key)
        if errors:
            raise UserError(
                _("The value for %(field)s field/s is mandatory in %(object_id)s")
                % {"field": ", ".join(errors), "object_id": object_id.name}
            )

    def _get_field_from_partner_or_parent_id(self, partner, field):
        return partner[field] or partner.parent_id and partner.parent_id[field] or ""

    def _get_deliverea_sender_info(self, partner, request_type):
        country_id = self._get_field_from_partner_or_parent_id(partner, "country_id")
        state_id = self._get_field_from_partner_or_parent_id(partner, "state_id")
        values = {
            "name": self._get_field_from_partner_or_parent_id(partner, "name"),
            "address": " ".join(
                [
                    self._get_field_from_partner_or_parent_id(partner, "street"),
                    self._get_field_from_partner_or_parent_id(partner, "street2"),
                ]
            ).strip(),
            "city": self._get_field_from_partner_or_parent_id(partner, "city"),
            "zipCode": self._get_field_from_partner_or_parent_id(partner, "zip"),
            "countryCode": country_id.code if country_id else "",
            "idNumber": self._get_field_from_partner_or_parent_id(partner, "vat"),
            "stateCode": state_id.code if state_id else "",
            "observations": "",
            "phone": self._get_field_from_partner_or_parent_id(partner, "phone")
            or self._get_field_from_partner_or_parent_id(partner, "mobile"),
            "email": self._get_field_from_partner_or_parent_id(partner, "email"),
        }
        self._check_mandatory_fields(
            values,
            MANDATORY_SENDER_FIELDS,
            partner,
        )
        return values

    def _get_deliverea_parcel_items(self, picking):
        items = []
        for move_line in picking.move_line_ids:
            items.append(
                {
                    "sku": move_line.product_id.barcode,
                    "description": move_line.product_id.name,
                    "amount": abs(move_line.move_id.sale_line_id.price_total),
                    "units": int(move_line.reserved_uom_qty),
                }
            )
        return items

    def _get_deliverea_parcel_info(self, carrier, picking):
        parcels = []
        num_packages = picking.number_of_packages or 1
        default_package = carrier.deliverea_default_packaging_id
        if (
            not default_package.max_weight
            or not default_package.height
            or not default_package.width
            or not default_package.packaging_length
        ):
            raise UserError(
                _(
                    "The max_weight, height, width and length values must be defined"
                    " in the package associated with the carrier."
                )
            )
        for i in range(num_packages):
            parcels.append(
                {
                    "weight": default_package.max_weight,
                    "height": default_package.height,
                    "width": default_package.width,
                    "length": default_package.packaging_length,
                }
            )
            if (
                i == 0
                and picking.picking_type_id.warehouse_id.partner_id.country_id.code
                != picking.partner_id.country_id.code
            ):
                parcels[0].update({"items": self._get_deliverea_parcel_items(picking)})
        return parcels

    def _get_service_attributes(self, carrier, service):
        values = {
            "cashOnDelivery": "0.0 EUR",
            "carrierNotifications": {
                "sms": carrier.deliverea_notifications_sms,
                "email": carrier.deliverea_notifications_email,
            },
            "saturdayDelivery": carrier.deliverea_saturday_delivery,
            "includeReturnLabel": carrier.deliverea_return_label,
            "returnProofOfDelivery": carrier.deliverea_return_label,
            "hideSender": carrier.deliverea_hide_sender,
            "insuranceValue": "0.0 EUR",
        }
        for parameter in service.deliverea_parameters:
            if parameter.name in values.keys():
                if parameter.type in ("ignored", "unsupported"):
                    del values[parameter.name]
                elif parameter.type == "required":
                    raise UserError(
                        _("The field %(parameter)s is required")
                        % {"parameter": parameter.name}
                    )
            else:
                # These keys have a different value in the dictionary of the API call
                # with respect to information received as a parameter
                if parameter.name == "notificationViaSMS" and parameter.type in (
                    "ignored",
                    "unsupported",
                ):
                    del values["carrierNotifications"]["sms"]
                elif parameter.name == "notificationViaEmail" and parameter.type in (
                    "ignored",
                    "unsupported",
                ):
                    del values["carrierNotifications"]["email"]
                if (
                    "carrierNotifications" in values.keys()
                    and len(values["carrierNotifications"]) == 0
                ):
                    del values["carrierNotifications"]
        return values

    def _prepare_deliverea_order(self, picking):
        carrier = picking.carrier_id
        service = carrier.deliverea_carrier_service_id
        request_type = "to" if picking.picking_type_code == "outgoing" else "from"
        payload = {
            request_type: self._get_deliverea_sender_info(
                picking.partner_id, request_type
            ),
            "carrierCode": service.carrier_code,
            "serviceCode": service.code,
            "costCenterCode": "DEFAULT",
            "distributionCenterId": carrier.deliverea_distribution_center_id.uuid,
            "clientReference": picking.name,
            "shippingDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "+00:00",
            "description": carrier.deliverea_description,
            "totalAmount": "{} {}".format(
                abs(picking.sale_id.amount_total) if picking.sale_id else 0,
                picking.sale_id.currency_id.name or self.company_id.currency_id.name,
            ),
            "parcels": self._get_deliverea_parcel_info(carrier, picking),
            "serviceAttributes": self._get_service_attributes(carrier, service),
            "clientAdditionalInfo": {
                "freeLabelText": hasattr(self, carrier.deliverea_note_selection_id.name)
                and getattr(self, carrier.deliverea_note_selection_id.name)
                or "",
            },
        }
        self._delete_empty_values(payload)
        self._check_mandatory_fields(payload, MANDATORY_SENDER_FIELDS, carrier)
        return payload

    def deliverea_send_shipping(self, pickings):
        res = []
        deliverea_request = DelivereaRequest(self)
        for picking in pickings:
            if picking.picking_type_code == "outgoing":
                vals = self._prepare_deliverea_order(picking)
                response = deliverea_request.create_shipment(vals)
                picking.write(
                    {
                        "deliverea_reference": response.get("delivereaReference", ""),
                        "carrier_tracking_ref": response.get("carrierReference", ""),
                    }
                )
                res.append(
                    {
                        "exact_price": 0,
                        "tracking_number": response.get("carrierReference", ""),
                    }
                )
                self.deliverea_get_label(picking)
            else:
                #  incoming moves are generated from the "generate pickup" button
                res.append(
                    {
                        "exact_price": 0,
                        "tracking_number": picking.carrier_tracking_ref,
                    }
                )
        return res

    def deliverea_get_return_label(self, pickings):
        self.deliverea_return_shipping(pickings)

    def deliverea_return_shipping(self, pickings):
        res = []
        deliverea_request = DelivereaRequest(self)
        for picking in pickings:
            vals = self._prepare_deliverea_order(picking)
            response = deliverea_request.create_return(vals)
            picking.write(
                {
                    "carrier_tracking_ref": response.get("carrierReference", ""),
                    "deliverea_reference": response.get("delivereaReference", ""),
                }
            )
        return res

    def deliverea_cancel_shipment(self, pickings):
        deliverea_request = DelivereaRequest(self)
        for picking in pickings:
            deliverea_request.delete_shipment(picking.deliverea_reference)
            picking.write({"deliverea_reference": False})

    def deliverea_get_label(self, pickings):
        deliverea_request = DelivereaRequest(self)
        for picking in pickings:
            if not picking.deliverea_reference:
                #  Recreate shipping and get label
                self.deliverea_send_shipping(picking)
            else:
                response = deliverea_request.get_shipment_label(
                    picking.deliverea_reference
                )
                if response:
                    file_type = response.get("type")
                    self.env["ir.attachment"].create(
                        {
                            "name": "%s.%s" % (picking.name, file_type),
                            "type": "binary",
                            "datas": response.get("content"),
                            "res_model": picking._name,
                            "res_id": picking.id,
                        }
                    )
            self.deliverea_tracking_state_update(picking)
        return True

    def deliverea_get_tracking_link(self, picking):
        domain = (
            self.deliverea_url_tracking
            if self.deliverea_url_tracking[-1] == "/"
            else self.deliverea_url_tracking + "/"
        )
        return "{}?q={}".format(domain, picking.deliverea_reference)

    def deliverea_tracking_state_update(self, picking):
        self.ensure_one()
        if not picking.deliverea_reference:
            return
        deliverea_request = DelivereaRequest(self)
        if picking.picking_type_code == "outgoing":
            tracking_events = deliverea_request.get_shipment_tracking(
                picking.deliverea_reference
            )
        else:
            tracking_events = deliverea_request.get_return_tracking(
                picking.deliverea_reference
            )
        if not tracking_events:
            return
        picking.tracking_state_history = "\n".join(
            [
                "- {}: [{}] {}".format(
                    event.get("occurredAt"), event.get("code"), event.get("message")
                )
                for event in tracking_events
            ]
        )
        tracking = tracking_events.pop()
        picking.tracking_state = "[{}] {}".format(
            tracking.get("code"), tracking.get("message")
        )
        deliverea_state = self.env["deliverea.state"].search(
            [("code", "=", tracking.get("code"))]
        )
        picking.delivery_state = deliverea_state.delivery_state
        if picking.delivery_state == "customer_delivered":
            picking.date_delivered = datetime.strftime(
                datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT
            )
