# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

from .ups_request import UpsRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("ups", "UPS")])
    ups_file_format = fields.Selection(
        selection=[("GIF", "PDF"), ("ZPL", "ZPL"), ("EPL", "EPL"), ("SPL", "SPL")],
        default="GIF",
        string="File format",
    )
    ups_ws_username = fields.Char(string="Username WS")
    ups_ws_password = fields.Char(string="Password WS")
    ups_access_license = fields.Char(string="Access license number")
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
        comodel_name="product.packaging", string="Default Packaging Type"
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

    def _get_ups_params(self, service):
        return {
            "prod": self.prod_environment,
            "service": service,
            "params": {
                "access_license_number": self.ups_access_license,
                "username": self.ups_ws_username,
                "password": self.ups_ws_password,
                "default_packaging_id": self.ups_default_packaging_id,
                "shipper_number": self.ups_shipper_number,
                "service_code": self.ups_service_code,
                "file_format": self.ups_file_format,
                "package_dimension_code": self.ups_package_dimension_code,
                "package_weight_code": self.ups_package_weight_code,
                "transaction_src": "Odoo (%s)" % self.env.cr.dbname,
            },
        }

    def ups_send_shipping(self, pickings):
        return [self.ups_create_shipping(p) for p in pickings]

    def ups_get_label(self, carrier_tracking_ref):
        """Generate label for picking
        :param picking - stock.picking record
        :returns attachment file
        """
        self.ensure_one()
        if not carrier_tracking_ref:
            return False
        ups_request = UpsRequest(**self._get_ups_params("label"))
        response = ups_request.shipping_label(carrier_tracking_ref)
        # Create attachment to add pdf label
        picking = self.env["stock.picking"].search(
            [("carrier_tracking_ref", "=", carrier_tracking_ref)]
        )
        LabelImageFormatCode = response["LabelImageFormat"]["Code"].upper()
        if LabelImageFormatCode != "GIF":
            attachment_name = "%s.pdf" % carrier_tracking_ref
        else:
            attachment_name = "%s-%s.%s" % (
                carrier_tracking_ref,
                LabelImageFormatCode,
                LabelImageFormatCode.lower(),
            )
        return self.env["ir.attachment"].create(
            {
                "name": attachment_name,
                "type": "binary",
                "datas": response["GraphicImage"],
                "res_model": picking._name,
                "res_id": picking.id,
            }
        )

    def ups_create_shipping(self, picking):
        """Send packages of the picking to UPS
        return a list of dicts {'exact_price': 'tracking_number':}
        suitable for delivery.carrier#send_shipping"""
        self.ensure_one()
        ups_request = UpsRequest(**self._get_ups_params("shipping"))
        response = ups_request._send_shipping(picking)
        picking.carrier_tracking_ref = response["ShipmentIdentificationNumber"]
        self.ups_get_label(picking.carrier_tracking_ref)
        return {
            "exact_price": response["price"],
            "tracking_number": picking.carrier_tracking_ref,
        }

    def ups_get_tracking_link(self, picking):
        return "https://ups.com/WebTracking/track?trackingNumber=%s" % (
            picking.carrier_tracking_ref
        )

    def ups_cancel_shipment(self, pickings):
        ups_request = UpsRequest(**self._get_ups_params("cancel"))
        return ups_request.cancel_shipment(pickings)

    def ups_tracking_state_update(self, picking):
        self.ensure_one()
        if (
            picking.carrier_id.ups_tracking_state_update_sync
            and picking.carrier_tracking_ref
        ):
            ups_request = UpsRequest(**self._get_ups_params("status"))
            response = ups_request.tracking_state_update(picking)
            picking.delivery_state = response["delivery_state"]
            picking.tracking_state_history = response["tracking_state_history"]

    def ups_rate_shipment(self, order):
        ups_request = UpsRequest(**self._get_ups_params("rate"))
        response = ups_request.rate_shipment(order)
        return {
            "success": True,
            "price": response,
            "error_message": False,
            "warning_message": False,
        }
