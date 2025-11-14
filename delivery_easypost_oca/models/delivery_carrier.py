from datetime import datetime

from markupsafe import Markup

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

from ..utils.pdf import assemble_pdf
from ..utils.zpl import assemble_zpl
from .easypost_request import EasypostRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    is_saturday_delivery = fields.Boolean("Delivery On Saturday?")
    delivery_type = fields.Selection(
        selection_add=[("easypost_oca", "Easypost OCA")],
        ondelete={
            "easypost_oca": lambda recs: recs.write(
                {"delivery_type": "fixed", "fixed_price": 0}
            )
        },
    )

    easypost_oca_test_api_key = fields.Char(
        "Easypost Test API Key",
        groups="base.group_system",
        help="Enter your API test key from Easypost account.",
    )
    easypost_oca_production_api_key = fields.Char(
        "Easypost Production API Key",
        groups="base.group_system",
        help="Enter your API production key from Easypost account",
    )

    easypost_oca_label_file_type = fields.Selection(
        [("PDF", "PDF"), ("ZPL", "ZPL"), ("EPL2", "EPL2")],
        string="Label Format",
        default="PDF",
    )

    easypost_oca_delivery_multiple_packages = fields.Selection(
        selection=[("shipments", "Shipments"), ("batch", "Batch")],
        string="Delivery Multiple Packages",
        default="shipments",
    )

    def easypost_oca_rate_shipment(self, order):
        """Return the rates for a quotation/SO."""
        ep_request = EasypostRequest(self)
        total_weight = self._easypost_oca_convert_weight(order._get_estimated_weight())
        parcel = {"weight": total_weight}
        recipient = self._prepare_address(order.partner_shipping_id)
        shipper = self._prepare_address(order.warehouse_id.partner_id)
        options = self._prepare_options()
        lowest_rate = ep_request.calculate_shipping_rate(
            to_address=recipient,
            from_address=shipper,
            parcel=parcel,
            options=options,
        )

        if not lowest_rate:
            raise UserError(_("No rate found for this shipping."))

        # Update price with the order currency
        rate = lowest_rate.get("rate", 0.0)
        currency = lowest_rate.get("currency", "USD")
        price = self._get_price_currency(
            rate=float(rate), currency=currency, order=order
        )

        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": False,
            "easypost_oca_carrier_name": lowest_rate.get("carrier", None),
            "easypost_oca_shipment_id": lowest_rate.get("shipment_id", None),
            "easypost_oca_rate_id": lowest_rate.get("id", None),
        }

    def easypost_oca_send_shipping(self, pickings) -> list:
        res = []
        ep_request = EasypostRequest(self)
        for picking in pickings:
            shipment = None
            price = 0.00
            tracking_code = ""
            shipping_data = {
                "exact_price": price,
                "tracking_number": tracking_code,
            }
            processed_shipments = []
            picking_shipments = self._prepare_shipments(picking)
            carrier_services = self._get_easypost_carrier_services(picking)
            carrier_services_params = {"carrier_services": carrier_services}

            if len(picking_shipments) > 1:
                # Create a batch with all shipments
                shipments = ep_request.create_multiples_shipments(
                    picking_shipments, **carrier_services_params
                )
                processed_shipments = ep_request.buy_shipments(
                    shipments, carrier_services=carrier_services
                )
                price, tracking_code = self._get_shipment_info(
                    processed_shipments,
                    picking.sale_id,
                )

                shipping_data.update(
                    {
                        "exact_price": price,
                        "tracking_number": tracking_code,
                    }
                )
                self._easypost_message_post(processed_shipments, picking)

            else:
                # Create a single shipment
                shipment = ep_request.create_shipment(
                    picking_shipments[0], **carrier_services_params
                )
                bought_shipment = ep_request.buy_shipment(
                    shipment, carrier_services=carrier_services
                )
                price, tracking_code = self._get_shipment_info(
                    [bought_shipment], picking.sale_id
                )

                shipping_data.update(
                    {
                        "exact_price": price,
                        "tracking_number": tracking_code,
                    }
                )

                picking.write(
                    {
                        "easypost_oca_shipment_id": bought_shipment.shipment_id,
                        "easypost_oca_rate_id": bought_shipment.rate,
                        "easypost_oca_carrier_id": bought_shipment.carrier_id,
                        "easypost_oca_carrier_name": bought_shipment.carrier_name,
                        "easypost_oca_carrier_service": bought_shipment.carrier_service,
                        "easypost_oca_tracking_url": bought_shipment.public_url,
                    }
                )
                self._easypost_message_post([bought_shipment], picking)

            res = res + [shipping_data]
        return res

    def easypost_oca_get_tracking_link(self, picking):
        return picking.easypost_oca_tracking_url

    def easypost_oca_cancel_shipment(self, pickings):
        raise UserError(_("You can't cancel Easypost shipping."))

    def _get_easypost_carrier_services(self, picking=None):
        return {}

    def _easypost_oca_convert_weight(self, weight):
        """Each API request for easypost required
        a weight in pounds.
        """
        if weight == 0:
            return weight
        weight_uom_id = self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter()
        weight_in_pounds = weight_uom_id._compute_quantity(
            weight, self.env.ref("uom.product_uom_lb")
        )
        weigth_in_ounces = max(
            0.1, float_round((weight_in_pounds * 16), precision_digits=1)
        )
        return weigth_in_ounces

    def _get_delivery_type(self):
        """Override of delivery to return the easypost delivery type."""
        res = super()._get_delivery_type()
        if self.delivery_type != "easypost":
            return res
        return self.easypost_delivery_type

    def _prepare_shipments(self, picking) -> list:
        shipments = []
        recipient = self._prepare_address(picking.partner_id)
        shipper = self._prepare_address(picking.picking_type_id.warehouse_id.partner_id)
        options = self._prepare_options(
            picking,
            self.easypost_oca_label_file_type,
            self.is_saturday_delivery,
        )
        carrier_accounts = self._prepare_carrier_account(picking)
        move_lines_with_package = picking.move_line_ids.filtered(
            lambda ml: ml.result_package_id
        )
        move_lines_without_package = picking.move_line_ids - move_lines_with_package
        if move_lines_without_package:
            # If the user didn't use a specific package we consider
            # that he put everything inside a single package.
            # The user still able to reorganise its packages if a
            # mistake happens.
            if picking.picking_type_code == "incoming":
                weight = sum(
                    ml.product_id.weight
                    * ml.product_uom_id._compute_quantity(
                        ml.quantity_product_uom,
                        ml.product_id.uom_id,
                        rounding_method="HALF-UP",
                    )
                    for ml in move_lines_without_package
                )
            else:
                weight = sum(
                    ml.product_id.weight
                    * ml.product_uom_id._compute_quantity(
                        ml.quantity,
                        ml.product_id.uom_id,
                        rounding_method="HALF-UP",
                    )
                    for ml in move_lines_without_package
                )

            parcel = self._prepare_parcel(
                weight=self._easypost_oca_convert_weight(weight)
            )

            shipments.append(
                {
                    "to_address": recipient,
                    "from_address": shipper,
                    "parcel": parcel,
                    "options": {
                        **options,
                        **{"print_custom_1": (picking.name if picking.name else "")},
                    },
                    "reference": picking.name if picking.name else "",
                    "carrier_accounts": carrier_accounts,
                }
            )

        if move_lines_with_package:
            # Generate an easypost shipment for each package in picking.
            for package in picking.package_ids:
                # compute move line weight in package
                move_lines = picking.move_line_ids.filtered(
                    lambda ml, pkg=package: ml.result_package_id == pkg
                )
                if picking.picking_type_code == "incoming":
                    weight = sum(
                        ml.product_id.weight
                        * ml.product_uom_id._compute_quantity(
                            ml.product_qty,
                            ml.product_id.uom_id,
                            rounding_method="HALF-UP",
                        )
                        for ml in move_lines
                    )
                else:
                    weight = package.shipping_weight

                parcel = self._prepare_parcel(
                    package=package.package_type_id,
                    weight=self._easypost_oca_convert_weight(weight),
                )
                shipments.append(
                    {
                        "to_address": recipient,
                        "from_address": shipper,
                        "parcel": parcel,
                        "options": {
                            **options,
                            **{
                                "print_custom_1": (package.name if package.name else "")
                            },
                        },
                        "reference": package.name if package.name else "",
                        "carrier_accounts": carrier_accounts,
                    }
                )

        return shipments

    def _prepare_parcel(self, package=None, weight: float = 0.0):
        parcel = {
            "weight": weight,
        }
        if package and package.package_carrier_type == "easypost_oca":
            if package.shipper_package_code:
                parcel.update({"predefined_package": package.shipper_package_code})
            if package.width > 0:
                parcel.update({"width": package.width})
            if package.height > 0:
                parcel.update({"height": package.height})
            if package.packaging_length > 0:
                parcel.update({"length": package.packaging_length})

        return parcel

    def _prepare_options(
        self,
        picking=None,
        easypost_oca_label_file_type: str = "PDF",
        is_saturday_delivery: bool = False,
    ):
        return {
            "label_date": datetime.now().isoformat(),
            "label_format": easypost_oca_label_file_type,
            "saturday_delivery": is_saturday_delivery,
        }

    def _prepare_carrier_account(self, picking) -> list:
        return []

    def _prepare_address(self, addr_obj):
        addr_fields = {
            "street1": "street",
            "street2": "street2",
            "city": "city",
            "zip": "zip",
            "phone": "phone",
            "email": "email",
        }
        address = {
            f"{field_name}": addr_obj[addr_obj_field]
            for field_name, addr_obj_field in addr_fields.items()
            if addr_obj[addr_obj_field]
        }
        address["name"] = addr_obj.name or addr_obj.display_name
        if addr_obj.state_id:
            address["state"] = addr_obj.state_id.code
        address["country"] = addr_obj.country_id.code
        if addr_obj.commercial_company_name:
            address["company"] = addr_obj.commercial_company_name
        return address

    def _get_price_currency(self, rate: float, currency: str, order=False) -> float:
        price = float(rate)
        currency_id = order.currency_id if order else self.env.company.currency_id
        if currency_id.name != currency:
            quote_currency = self.env["res.currency"].search(
                [("name", "=", currency)], limit=1
            )
            price = quote_currency._convert(
                price,
                currency_id,
                self.env.company,
                fields.Date.today(),
            )
        return price

    def _easypost_message_post(self, shipments, picking, batch_mode=False):
        carrier_tracking_links: list[str] = []
        files_to_merge: list = []

        for shipment in shipments:
            public_url = (
                shipment.tracker.get("public_url", "")
                if batch_mode
                else shipment.public_url
            )
            tracking_code = (
                shipment.tracker.get("tracking_code", "")
                if batch_mode
                else shipment.tracking_code
            )
            carrier_tracking_links.append(
                (
                    Markup("<a target='_blank' href='%(url)s'> %(code)s</a>")
                    % {
                        "url": public_url,
                        "code": tracking_code,
                    },
                    shipment.carrier_name,
                    shipment.carrier_service,
                )
            )
            files_to_merge.append(shipment.get_label_content())

        logmessage = Markup(
            "Shipment created into Easypost<br/>"
            "<b>Tracking Numbers:</b> %(tracking)s<br/>"
            "<b>Carrier Account:</b> %(carrier)s<br/>"
            "<b>Carrier Service:</b> %(service)s<br/>"
        ) % {
            "tracking": ", ".join([link[0] for link in carrier_tracking_links]),
            "carrier": ", ".join({link[1] for link in carrier_tracking_links}),
            "service": ", ".join({link[2] for link in carrier_tracking_links}),
        }

        file_merged = self._contact_files(
            self.easypost_oca_label_file_type, files_to_merge
        )
        labels = [
            (
                f"Label-{picking.name}.{self.easypost_oca_label_file_type.lower()}",
                file_merged,
            )
        ]
        picking.message_post(body=logmessage, attachments=labels)

    def _get_shipment_info(self, shipments, sale_id, batch_mode=False):
        price, tracking_code = (0.0, "")
        if batch_mode:
            price = sum(
                self._get_price_currency(
                    float(shipment.selected_rate.get("rate", 0.0)),
                    shipment.selected_rate.get("currency"),
                    sale_id,
                )
                for shipment in shipments
            )
            tracking_code = ", ".join(
                [shipment.tracker.get("tracking_code", "") for shipment in shipments]
            )
        else:
            price = sum(
                self._get_price_currency(
                    shipment.rate,
                    shipment.currency,
                    sale_id,
                )
                for shipment in shipments
            )
            tracking_code = ", ".join(
                [shipment.tracking_code for shipment in shipments]
            )

        return price, tracking_code

    @staticmethod
    def _contact_files(f_type, files):
        if f_type == "PDF":
            return assemble_pdf(files)
        elif f_type == "ZPL":
            return assemble_zpl(files)

        return files
