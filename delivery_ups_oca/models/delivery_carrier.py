# Copyright 2020 Hunki Enterprises BV
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# Copyright 2023 ForgeFlow, S.L. - Jordi Ballester
# Copyright 2024 Sygel - Manuel Regidor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .ups_request import UpsRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("ups", "UPS")],
        ondelete={
            "ups": lambda recs: recs.write({"delivery_type": "fixed", "fixed_price": 0})
        },
    )
    ups_file_format = fields.Selection(
        selection=[("GIF", "GIF"), ("ZPL", "ZPL"), ("EPL", "EPL"), ("SPL", "SPL")],
        default="GIF",
        string="File format",
    )
    ups_shipper_number = fields.Char(string="Shipper number")
    ups_service_code = fields.Selection(
        selection=[
            ("01", "Next Day Air"),
            ("02", "2nd Day Air"),
            ("03", "Ground"),
            ("07", "Express"),
            ("08", "Expedited"),
            ("11", "UPS Standard"),
            ("12", "3 Day Select"),
            ("13", "Next Day Air Saver"),
            ("14", "UPS Next Day Air® Early"),
            ("17", "UPS Worldwide Economy DDU"),
            ("54", "Express Plus"),
            ("59", "2nd Day Air A.M."),
            ("65", "UPS Saver"),
            ("M2", "First Class Mail"),
            ("M3", "Priority Mail"),
            ("M4", "Expedited Mail Innovations"),
            ("M5", "Priority Mail Innovations"),
            ("M6", "Economy Mail Innovations"),
            ("M7", "Mail Innovations (MI) Returns"),
            ("70", "UPS Access PointTM Economy"),
            ("71", "UPS Worldwide Express Freight Midday"),
            ("72", "UPS Worldwide Economy"),
            ("74", "UPS Express®12:00"),
            ("82", "UPS Today Standard"),
            ("83", "UPS Today Dedicated Courier"),
            ("84", "UPS Today Intercity"),
            ("85", "UPS Today Express"),
            ("86", "UPS Today Express Saver"),
            ("96", "UPS Worldwide Express Freight"),
        ],
        default="11",
        string="Service code",
    )
    ups_default_packaging_id = fields.Many2one(
        comodel_name="product.packaging",
        string="Default Packaging Type",
        domain=[("package_carrier_type", "=", "ups")],
    )
    ups_package_dimension_code = fields.Selection(
        selection=[("IN", "IN"), ("CM", "CM")],
        default="IN",
        string="Package Dimension code",
        help="Is necessary to set dimension code from packages in shipping "
        "creation process",
    )
    ups_package_weight_code = fields.Selection(
        selection=[("LBS", "LBS"), ("KGS", "KGS"), ("OZS", "OZS")],
        default="LBS",
        string="Package Weight code",
        help="Is necessary to set weight code from packages in shipping creation "
        "process",
    )
    ups_tracking_state_update_sync = fields.Boolean(
        string="Tracking state update sync",
        help="If checked, odoo try to state update from picking according to UPS "
        "webservice (you will necessary to activate tracking API)",
    )
    ups_use_packages_from_picking = fields.Boolean(string="Use packages from picking")
    ups_client_id = fields.Char()
    ups_client_secret = fields.Char()
    ups_token = fields.Char()
    ups_token_expiration_date = fields.Datetime(readonly=True)
    ups_cash_on_delivery = fields.Boolean(string="UPS Cash On Delivery")
    ups_cod_funds_code = fields.Selection(
        selection=[("1", "Cash"), ("9", "Check/Cashier Check/Money Order")],
        string="UPS Cod Funds Code",
    )

    def _ups_get_response_price(self, total_charges, currency, company):
        """We need to convert the price if the currency is different."""
        price = float(total_charges["MonetaryValue"])
        if total_charges["CurrencyCode"] != currency.name:
            price = currency._convert(
                price,
                self.env["res.currency"].search(
                    [("name", "=", total_charges["CurrencyCode"])]
                ),
                company,
                fields.Date.today(),
            )
        return price

    def ups_rate_shipment(self, order):
        ups_request = UpsRequest(self)
        response = ups_request.rate_shipment(order)
        price = self._ups_get_response_price(
            response, order.currency_id, order.company_id
        )
        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": False,
        }

    def ups_create_shipping(self, picking):
        """Send packages of the picking to UPS
        return a list of dicts {'exact_price': 'tracking_number':}
        suitable for delivery.carrier#send_shipping"""
        self.ensure_one()
        ups_request = UpsRequest(self)
        response = ups_request._send_shipping(picking)
        extra_price = self._ups_get_response_price(
            response["price"], picking.company_id.currency_id, picking.company_id
        )
        picking.carrier_tracking_ref = response["ShipmentIdentificationNumber"]
        # Create label from response
        self._create_ups_label(picking, response["labels"])
        # Return
        return {
            "exact_price": extra_price,
            "tracking_number": picking.carrier_tracking_ref,
        }

    def ups_send_shipping(self, pickings):
        return [self.ups_create_shipping(p) for p in pickings]

    def _prepare_ups_label_attachment(self, picking, values):
        return {
            "name": values["name"],
            "type": "binary",
            "datas": values["datas"],
            "res_model": picking._name,
            "res_id": picking.id,
        }

    def _create_ups_label(self, picking, labels):
        val_list = []
        for label in labels:
            format_code = label["format_code"].upper()
            attachment_name = "%s-%s.%s" % (
                label["tracking_ref"],
                format_code,
                format_code,
            )
            val_list.append(
                self._prepare_ups_label_attachment(
                    picking,
                    {
                        "name": attachment_name,
                        "datas": label["datas"],
                    },
                )
            )
        return self.env["ir.attachment"].create(val_list)

    def ups_get_label(self, carrier_tracking_ref):
        """Generate label for picking
        :param picking - stock.picking record
        :returns attachment file
        """
        self.ensure_one()
        if not carrier_tracking_ref:
            return False
        ups_request = UpsRequest(self)
        response = ups_request.shipping_label(carrier_tracking_ref)
        # Create attachment to add pdf label
        picking = self.env["stock.picking"].search(
            [("carrier_tracking_ref", "=", carrier_tracking_ref)]
        )
        return self._create_ups_label(picking, response)

    def ups_get_tracking_link(self, picking):
        return "https://ups.com/WebTracking/track?trackingNumber=%s" % (
            picking.carrier_tracking_ref
        )

    def ups_cancel_shipment(self, pickings):
        ups_request = UpsRequest(self)
        for picking in pickings.filtered(lambda a: a.carrier_tracking_ref):
            if ups_request.cancel_shipment(pickings):
                picking.write({"tracking_state_history": False})
        return True

    def ups_tracking_state_update(self, picking):
        self.ensure_one()
        if (
            picking.carrier_id.ups_tracking_state_update_sync
            and picking.carrier_tracking_ref
        ):
            ups_request = UpsRequest(self)
            response = ups_request.tracking_state_update(picking)
            picking.delivery_state = response["delivery_state"]
            picking.tracking_state_history = response["tracking_state_history"]

    def ups_update_token(self):
        self.ensure_one()
        ups_request = UpsRequest(self)
        ups_request._get_new_token()
