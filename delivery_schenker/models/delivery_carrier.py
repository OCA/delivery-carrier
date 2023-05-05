# Copyright 2021 Tecnativa - David Vidal
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .schenker_request import SchenkerRequest

SCHENKER_STATUS_CODES = {
    "ENT": ("Booked", "shipping_recorded_in_carrier"),
    "COL": ("Collected", "shipping_recorded_in_carrier"),
    "DET": ("Delivered to terminal by shipper", "in_transit"),
    "ENM": ("Arrived", "in_transit"),
    "MAN": ("Departed", "in_transit"),
    "DIS": ("To Consignee's Disposal", "warehouse_delivered"),
    "DOT": ("Out for Delivery", "in_transit"),
    "PUP": ("Picked up by consignee", "customer_delivered"),
    "DLV": ("Delivered", "customer_delivered"),
    "NDL": ("Not delivered", "canceled_shipment"),
}


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("schenker", "DB Schenker")],
        ondelete={"schenker": "set default"},
    )
    schenker_access_key = fields.Char(string="Access Key", help="Schenker Access Key")
    schenker_group_id = fields.Char(string="Group")
    schenker_user = fields.Char(string="User")
    schenker_booking_type = fields.Selection(
        selection=[
            ("land", "Land"),
            ("air", "Air"),
            ("ocean_fcl", "Ocean FCL"),
            ("ocean_lcl", "Ocean LCL"),
        ],
        default="land",
        string="Booking Type",
        help="Choose Schenker booking type. Only land is currently supported",
    )
    schenker_barcode_format = fields.Selection(
        selection=[("A4", "A4"), ("A6", "A6")], default="A6", string="Barcode Format"
    )
    schenker_barcode_mail = fields.Char(
        string="Barcode Copy Email",
        help="Optional: send a barcode copy to this email address",
    )
    schenker_barcode_a4_start_pos = fields.Integer(
        string="Barcode Start Position",
        default=1,
        help="For A4 format you can define the starting position",
    )
    schenker_barcode_a4_separated = fields.Boolean(
        string="Barcode Separated",
        default=False,
        help="For A4 define if the labels shall be printed on separate pages",
    )
    schenker_incoterm_id = fields.Many2one(
        comodel_name="account.incoterms",
        string="Default Incoterm",
        help="It will be overriden by the sale order one if it's specified.",
    )
    schenker_service_type = fields.Selection(
        string="Service Type",
        help="Defines service type: D2D, D2P, P2D, P2P, D2A, A2D, A2A. Depending on "
        "the Transport mode the service will be validated. For instance if the "
        "transport mode is AIR, the service type A2A (AirportToAirport)",
        selection=[
            ("D2D", "Door-to-door"),
            ("D2P", "Door-to-port"),
            ("P2D", "Port-to-door"),
            ("D2A", "Door-to-airport"),
            ("A2D", "Airport-to-door"),
            ("A2A", "Aiport-to-airport"),
        ],
    )
    schenker_service_land = fields.Selection(
        string="Land service",
        help="Land shipping product options. Depending on your customer account, some "
        "services could not be available",
        selection=[
            ("CON", "DBSchenkerconcepts"),
            ("DIR", "DBSchenkerdirects"),
            ("LPA", "DBSchenkerparcel Logistics Parcel"),
            ("PAL", "DBSchenkerpallets"),
            ("PRI", "DBSchenkerprivpark"),
            ("auc0", "austroexpress PUNKT 10"),
            ("auc2", "austroexpress PUNKT 12"),
            ("auc8", "austroexpress PUNKT 8"),
            ("aucc", "austroexpress PUNKT 17"),
            ("auco", "austrocargo"),
            ("ecsp", "SCHENKERsystem-plus"),
            ("ect1", "DB SCHENKERspeed 10"),
            ("ect2", "DB SCHENKERspeed 12"),
            ("sch2", "DB SCHENKERtop 12"),
            ("schs", "DB SCHENKERsystem international"),
            ("sysd", "DB SCHENKERsystem domestic"),
            ("scht", "DB SCHENKERtop"),
            ("schx", "DB SCHENKERsystem fix"),
            ("ecpa", "DB SCHENKERparcel"),
            ("ect8", "DB SCHENKERspeed 8"),
            ("ectn", "DB SCHENKERspeed"),
            ("40", "DB SCHENKERsystem classic"),
            ("41", "DB SCHENKERsystem speed"),
            ("42", "DB SCHENKERsystem fixday"),
            ("43", "DBSchenker System"),
            ("44", "DBSchenker System Premium"),
            ("71", "DB SCHENKERdirect"),
        ],
    )
    schenker_service_air = fields.Selection(
        string="Air service",
        help="Air shipping product options. Depending on your customer account, some "
        "services could not be available",
        selection=[
            ("f", "DB SCHENKERjetcargo first"),
            ("s", "DB SCHENKERjetcargo special"),
            ("b", "DB SCHENKERjetcargo business"),
            ("e", "DB SCHENKERjetcargo economy"),
            ("eagd", "DB SCHENKERjetexpress gold"),
            ("easv", "DB SCHENKERjetexpress silver"),
        ],
    )
    schenker_indoor_delivery = fields.Boolean(
        string="Indoor Delivery", help="Defines if indoor delivery is required"
    )
    schenker_express = fields.Boolean(
        string="Express", help="Defines if shipment is express"
    )
    schenker_food_related = fields.Boolean(
        string="Food Related", help="Defines if shipment is food related"
    )
    schenker_heated_transport = fields.Boolean(
        string="Heated Transport",
        help="Defines if shipment is required heated transport",
    )
    schenker_home_delivery = fields.Boolean(
        string="Home Delivery", help="Defines if shipment is required home delivery"
    )
    schenker_own_pickup = fields.Boolean(
        string="Own Pickup", help="Defines if shipment is required own pickup"
    )
    schenker_pharmaceuticals = fields.Boolean(
        string="Pharmaceuticals", help="Defines if shipment is pharmaceutical"
    )
    schenker_measure_unit = fields.Selection(
        string="Measure Unit",
        help="The proper request will be formed accordingly from the picking",
        selection=[
            ("VOLUME", "Volume"),
            ("LOADING_METERS", "Loading meters"),
            ("PIECES", "Pieces"),
            ("PALLET_SPACE", "Pallet space"),
        ],
        default="VOLUME",
    )
    schenker_default_packaging_id = fields.Many2one(
        comodel_name="product.packaging",
        string="Default Package Type",
        domain=[("package_carrier_type", "=", "schenker")],
        help="If not delivery package or the package doesn't have defined the packaging"
        "it will default to this type",
    )
    schenker_address_number = fields.Char(
        "Address ID",
        help="ID assigned by Schenker to you.\nWill be part of the sender or "
        "if set, the invoice address.",
    )
    schenker_partner_invoice_id = fields.Many2one(
        "res.partner",
        "Invoice Address",
        ondelete="restrict",
        help="If set, this contact will be sent as invoice address to Schenker."
        "\nIf Address ID is set, it will be part of it instead of the sender",
    )

    def _get_schenker_credentials(self):
        """Access key is mandatory for every request while group and user are
        optional"""
        credentials = {
            "prod": self.prod_environment,
            "access_key": self.schenker_access_key,
        }
        if self.schenker_group_id:
            credentials["group_id"] = self.schenker_group_id
        if self.schenker_user:
            credentials["user"] = self.schenker_user
        return credentials

    @api.model
    def _schenker_log_request(self, schenker_request, picking):
        """Helper to write raw request/response to the current picking. If debug
        is active in the carrier, those will be logged in the ir.logging as well"""
        schenker_last_request = schenker_last_response = False
        try:
            schenker_last_request = etree.tostring(
                schenker_request.history.last_sent["envelope"],
                encoding="UTF-8",
                pretty_print=True,
            )
            schenker_last_response = etree.tostring(
                schenker_request.history.last_received["envelope"],
                encoding="UTF-8",
                pretty_print=True,
            )
        # Don't fail hard on this. Sometimes zeep could not be able to keep history
        except Exception:
            return
        # Debug must be active in the carrier
        self.log_xml(schenker_last_request, "schenker_request")
        self.log_xml(schenker_last_response, "schenker_response")

    def _prepare_schenker_barcode(self):
        """Always request the barcode label when generating the booking. We can choose
        between two formats: A6 and A4, where an starting position can be set"""
        vals = {"barcodeRequest": self.schenker_barcode_format}
        if self.schenker_barcode_mail:
            vals["barcodeRequestEmail"] = self.schenker_barcode_mail
        if self.schenker_barcode_format == "A6":
            return vals
        # This options only can be informed when the label format is A4
        vals.update(
            {
                "start_pos": self.schenker_barcode_a4_start_pos,
                "separated": self.schenker_barcode_a4_separated,
            }
        )
        return vals

    def _schenker_address_optional_fields(self):
        return [
            ("email", "email"),
            ("mobilePhone", "mobile"),
            ("phone", "phone"),
            ("street2", "street2"),
            ("stateCode", "state_id.code"),
            ("stateName", "state_id.name"),
        ]

    def _prepare_schenker_address(
        self,
        partner,
        address_type="CONSIGNEE",
        location_type="PHYSICAL",
        person_type="COMPANY",
    ):
        """Generic for any address type. The address from the one receiving the goods.
        Keep in mind that every country could have their own mandatory fields rules,
        so the request could fail if those fields aren't filled on the contact. An
        informative error should raise though.
        :param res.partner record
        :returns dicts with shipping address formated for Scheneket API
        """
        vals = {
            "type": address_type,
            "name1": partner.name,
            "locationType": location_type,  # POSTAL or PHYSICAL
            "personType": person_type,  # PERSON OR COMPANY
            "street": partner.street,
            "postalCode": partner.zip,
            "city": partner.city,
            "countryCode": partner.country_id.code,
            "preferredLanguage": self.env["res.lang"]._lang_get(partner.lang).iso_code,
        }
        # Optional stuff. The API doesn't like falsy or empty request fields
        for schenker_key, expression in self._schenker_address_optional_fields():
            value = partner
            for field in expression.split("."):
                value = getattr(value, field)
            if not value:
                continue
            vals[schenker_key] = value
        return vals

    def _schenker_shipping_address(self, picking):
        """Each booking should have at least 2 addresses of types: SHIPPER and CONSIGNEE
        Other options are: PICKUP, DELIVERY, NOTIFY, INVOICE and could be hooked to this
        method to include them in the booking request.
        :param picking record
        :returns list of dicts with shipping addresses formated for Scheneket API
        """
        shipper_address = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        consignee_address = picking.partner_id
        shipper_address = self._prepare_schenker_address(shipper_address, "SHIPPER")
        consignee_address = self._prepare_schenker_address(consignee_address)
        result = [
            shipper_address,
            consignee_address,
        ]
        invoice_address = False
        if self.schenker_partner_invoice_id:
            invoice_address = self._prepare_schenker_address(
                self.schenker_partner_invoice_id, "INVOICE"
            )
            result.append(invoice_address)
        if self.schenker_address_number:
            (invoice_address or shipper_address)[
                "schenkerAddressId"
            ] = self.schenker_address_number
        return result

    def _schenker_shipping_product(self):
        """Gets the proper shipping product according to the shipping type
        :returns string with shipping product code
        """
        type_mapping = {
            "air": self.schenker_service_air,
            "land": self.schenker_service_land,
            "ocean_fcl": "fcl",
            "ocean_lcl": "lcl",
        }
        return type_mapping[self.schenker_booking_type]

    def _schenker_metric_system(self):
        """
        :returns string with schenker metric system (METRIC or IMPERIAL)
        """
        get_param = self.env["ir.config_parameter"].sudo().get_param
        product_weight_in_lbs_param = get_param("product.weight_in_lbs", "0")
        return "IMPERIAL" if product_weight_in_lbs_param == "1" else "METRIC"

    def _schenker_pickup_dates(self, picking):
        """Convert picking dates for schenker api. We're taking the whole delivery
        day as picking windows, although a more complex solution could be provided.
        :param picking record with picking to send
        :returns dict values with the picking dates in iso format
        """
        date_from = fields.Datetime.context_timestamp(
            self, picking.date_done.replace(hour=0, minute=0, second=0)
        ).isoformat()
        date_to = fields.Datetime.context_timestamp(
            self, picking.date_done.replace(hour=23, minute=59, second=59)
        ).isoformat()
        return {"pickUpDateFrom": date_from, "pickUpDateTo": date_to}

    def _schenker_shipping_information_package(self, picking, package):
        weight = package.shipping_weight or package.weight
        # Volume calculations can be unfolded with stock_quant_package_dimension
        if hasattr(package, "volume"):
            volume = round(package.volume, 2)
        else:
            volume = sum([q.quantity * q.product_id.volume for q in package.quant_ids])
        return {
            # Dangerous goods is not supported
            "dgr": False,
            "cargoDesc": picking.name + " / " + package.name,
            "grossWeight": round(weight, 2),
            # Default to 1 if no volume informed
            "volume": volume or 0.01,
            "packageType": (
                package.packaging_id.shipper_package_code
                or self.schenker_default_packaging_id.shipper_package_code
            ),
            "stackable": (
                package.packaging_id.schenker_stackable
                or self.schenker_default_packaging_id.schenker_stackable
            ),
            "pieces": 1,
        }

    def _schenker_shipping_information(self, picking):
        """When we don't use delivery packages, we'll deliver everything in one single
        shipping info. Otherwise, we'll get the info for each package.
        :param picking record with picking to deliver
        :returns list of dicts with delivery packages shipping info
        """
        if picking.package_level_ids and picking.package_ids:
            return [
                self._schenker_shipping_information_package(picking, package)
                for package in picking.package_ids
            ]
        weight = picking.shipping_weight or picking.weight
        # Obviously products should be well configured. This parameter is mandatory.
        volume = sum(
            [
                ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                * ml.product_id.volume
                for ml in picking.move_line_ids
            ]
        )
        return [
            {
                # Dangerous goods is not supported
                "dgr": False,
                "cargoDesc": picking.name,
                # For a more complex solution use packaging properly
                "grossWeight": round(weight / picking.number_of_packages, 2),
                "volume": round(volume, 2) or 0.01,
                "packageType": self.schenker_default_packaging_id.shipper_package_code,
                "stackable": self.schenker_default_packaging_id.schenker_stackable,
                "pieces": picking.number_of_packages,
            }
        ]

    def _schenker_measures(self, picking, vals):
        """Only volume is supported as a pallet calculations structure should be
        provided to use the other API options. This hook can be used to communicate
        with the API in the future
        :param picking record with picking to deliver
        :returns dict values for the proper unit key and value
        """
        if self.schenker_measure_unit == "VOLUME":
            return {"measureUnitVolume": vals["shippingInformation"]["volume"]}
        return {}

    def _prepare_schenker_shipping(self, picking):
        """Convert picking values for schenker api
        :param picking record with picking to send
        :returns dict values for the connector
        """
        self.ensure_one()
        picking.ensure_one()
        # We'll compose the request via some diferenced parts, like label settings,
        # address options, incoterms and so. There are lots of thing to take into
        # account to acomplish a properly formed request.
        vals = {}
        vals.update(self._prepare_schenker_barcode())
        shipping_information = self._schenker_shipping_information(picking)
        vals.update(
            {
                "address": self._schenker_shipping_address(picking),
                "incoterm": (
                    picking.sale_id.incoterm.code or self.schenker_incoterm_id.code
                ),
                # A maximum of 35 characters is supported
                "incotermLocation": picking.partner_id.display_name[:35],
                "productCode": self._schenker_shipping_product(),
                "measurementType": self._schenker_metric_system(),
                "grossWeight": round(picking.shipping_weight, 2),
                "shippingInformation": {
                    "shipmentPosition": shipping_information,
                    "grossWeight": round(picking.shipping_weight, 2),
                    "volume": sum(info["volume"] for info in shipping_information),
                },
                "measureUnit": self.schenker_measure_unit,
                # Customs Clearance not supported for now as it needs a full customs
                # implementation
                "customsClearance": False,
                # Defines a business scenario where the Schenker customer sends a
                # booking request in the name of his ordering party
                "neutralShipping": False,
                "pickupDates": self._schenker_pickup_dates(picking),
                # Not supported for the moment
                "specialCargo": False,
                "specialCargoDescription": False,
                "serviceType": self.schenker_service_type,
                "indoorDelivery": self.schenker_indoor_delivery,
                "express": self.schenker_express,
                "foodRelated": self.schenker_food_related,
                "heatedTransport": self.schenker_heated_transport,
                "homeDelivery": self.schenker_home_delivery,
                "ownPickup": self.schenker_own_pickup,
                "pharmaceuticals": self.schenker_pharmaceuticals,
            }
        )
        vals.update(self._schenker_measures(picking, vals))
        return vals

    def schenker_send_shipping(self, pickings):
        """Send booking request to Schenker
        :param pickings: A recordset of pickings
        :return list: A list of dictionaries although in practice it's
        called one by one and only the first item in the dict is taken. Due
        to this design, we have to inject vals in the context to be able to
        add them to the message.
        """
        schenker_request = SchenkerRequest(**self._get_schenker_credentials())
        result = []
        for picking in pickings:
            vals = self._prepare_schenker_shipping(picking)
            vals.update({"tracking_number": False, "exact_price": 0})
            try:
                response = schenker_request._send_shipping(
                    vals, self.schenker_booking_type
                )
            except Exception as e:
                raise (e)
            finally:
                self._schenker_log_request(schenker_request, picking)
            if not response:
                result.append(vals)
                continue
            vals["tracking_number"] = response.get("booking_id")
            # We post an extra message in the chatter with the barcode and the
            # label because there's clean way to override the one sent by core.
            body = _("Schenker Shipping barcode document")
            attachment = []
            if response.get("barcode"):
                attachment = [
                    (
                        "schenker_label_{}.pdf".format(response.get("booking_id")),
                        response.get("barcode"),
                    )
                ]
            picking.message_post(body=body, attachments=attachment)
            result.append(vals)
        return result

    def schenker_cancel_shipment(self, pickings):
        """Cancel the expedition
        :param pickings - stock.picking recordset
        :returns pdf file
        """
        schenker_request = SchenkerRequest(**self._get_schenker_credentials())
        for picking in pickings.filtered("carrier_tracking_ref"):
            try:
                schenker_request._cancel_shipment(picking.carrier_tracking_ref)
            except Exception as e:
                raise (e)
            finally:
                self._schenker_log_request(schenker_request, picking)
        return True

    def schenker_get_label(self, reference):
        """Generate label for picking
        :param picking - stock.picking record
        :returns pdf file
        """
        self.ensure_one()
        if not reference:
            return False
        schenker_request = SchenkerRequest(**self._get_schenker_credentials())
        format_vals = self.schenker_barcode_format
        if format_vals == "A4":
            format_vals = {
                "start_pos": self.schenker_barcode_a4_start_pos,
                "_value_1": self.schenker_barcode_format,
            }
        label = schenker_request._shipping_label([reference], format_vals)
        if not label:
            return False
        return label

    def schenker_get_tracking_link(self, picking):
        """Provide tracking link for the customer"""
        return (
            "https://eschenker.dbschenker.com/app/tracking-public/?refNumber=%s"
            % picking.carrier_tracking_ref
        )

    def _prepare_schenker_tracking(self, picking):
        self.ensure_one()
        return {
            "reference": picking.carrier_tracking_ref,
            "reference_type": "cu",
            "booking_type": self.schenker_booking_type,
        }

    def schenker_tracking_state_update(self, picking):
        """Tracking state update"""
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        schenker_request = SchenkerRequest(
            **self._get_schenker_credentials(), service="tracking"
        )
        response = schenker_request._get_tracking_states(
            **self._prepare_schenker_tracking(picking)
        )
        if response.get("shipment"):
            shipment = response.get("shipment")[0]
            info = shipment.ShipmentInfo.ShipmentBasicInfo
            status_event_list = info.StatusEventList.StatusEvent
            last_event = SCHENKER_STATUS_CODES.get(info.LastEvent, ("",))
            picking.write(
                {
                    "tracking_state_history": (
                        "\n".join(
                            [
                                "{} {} {} - [{}] {}".format(
                                    fields.Datetime.from_string(t.Date).strftime(
                                        "%d/%m/%Y"
                                    ),
                                    t.Time.strftime("%H:%M:%S"),
                                    t.OccurredAt.LocationName,
                                    t.Status,
                                    t.StatusDescription._value_1,
                                )
                                for t in status_event_list
                            ]
                        )
                    ),
                    "tracking_state": "[{}] {}".format(info.LastEvent, last_event[0]),
                    "delivery_state": last_event[1],
                }
            )
        return

    def schenker_rate_shipment(self, order):
        """There's no public API so another price method should be used."""
        return {
            "success": True,
            "price": self.product_id.lst_price,
            "error_message": _(
                "Schenker API doesn't provide methods to compute delivery "
                "rates, so you should relay on another price method instead or "
                "override this one in your custom code."
            ),
            "warning_message": _(
                "Schenker API doesn't provide methods to compute delivery "
                "rates, so you should relay on another price method instead or "
                "override this one in your custom code."
            ),
        }

    # UX Control over not implemented features.

    @api.onchange("schenker_booking_type")
    def onchange_schenker_booking_type(self):
        """Avoid by UX that the user could choose another shipping method. In
        the future, this can be removed as long as those method have the proper
        support"""
        if self.schenker_booking_type != "land":
            raise UserError(_("Only land shipping is currently supported"))

    @api.onchange("schenker_measure_unit")
    def onchange_schenker_measure_unit(self):
        """Avoid by UX that the user could choose another measure unit. Proper pallet
        calculation structure should be provided to use the other API options. A hook
        method is provided though."""
        if self.schenker_measure_unit != "VOLUME":
            raise UserError(_("Only volume is currently supported"))
