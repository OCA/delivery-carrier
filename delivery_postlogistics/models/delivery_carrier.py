# Copyright 2013 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..postlogistics.web_service import PostlogisticsWebService


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("postlogistics", "PostLogistics")],
        ondelete={"postlogistics": "set default"},
    )
    postlogistics_default_package_type_id = fields.Many2one(
        "stock.package.type",
        domain=[("package_carrier_type", "=", "postlogistics")],
        default=lambda self: self._default_postlogistics_default_package_type_id(),
    )
    postlogistics_endpoint_url = fields.Char(
        string="Endpoint URL",
        default="https://wedecint.post.ch/",
        required=True,
    )
    postlogistics_client_id = fields.Char(
        string="Client ID", groups="base.group_system"
    )
    postlogistics_client_secret = fields.Char(
        string="Client Secret", groups="base.group_system"
    )
    postlogistics_logo = fields.Binary(
        string="Company Logo on Post labels",
        help="Optional company logo to show on label.\n"
        "If using an image / logo, please note the following:\n"
        "– Image width: 47 mm\n"
        "– Image height: 25 mm\n"
        "– File size: max. 30 kb\n"
        "– File format: GIF or PNG\n"
        "– Colour table: indexed colours, max. 200 colours\n"
        "– The logo will be printed rotated counter-clockwise by 90°"
        "\n"
        "We recommend using a black and white logo for printing in "
        " the ZPL2 format.",
    )
    postlogistics_office = fields.Char(
        string="Domicile Post office",
        help="Post office which will receive the shipped goods",
    )
    postlogistics_label_layout = fields.Many2one(
        comodel_name="delivery.carrier.template.option",
        string="Label layout",
        domain=[("type", "=", "label_layout")],
    )
    postlogistics_output_format = fields.Many2one(
        comodel_name="delivery.carrier.template.option",
        string="Output format",
        domain=[("type", "=", "output_format")],
    )
    postlogistics_resolution = fields.Many2one(
        comodel_name="delivery.carrier.template.option",
        string="Resolution",
        domain=[("type", "=", "resolution")],
    )
    postlogistics_tracking_format = fields.Selection(
        [
            ("postlogistics", "Use default postlogistics tracking numbers"),
            ("picking_num", "Use picking number with pack counter"),
        ],
        string="Tracking number format",
        default="postlogistics",
        help="Allows you to define how the ItemNumber (the last 8 digits) "
        "of the tracking number will be generated:\n"
        "- Default postlogistics numbers: The webservice generates it"
        " for you.\n"
        "- Picking number with pack counter: Generate it using the "
        "digits of picking name and add the pack number. 2 digits for"
        "pack number and 6 digits for picking number. (eg. 07000042 "
        "for picking 42 and 7th pack",
    )
    postlogistics_proclima_logo = fields.Boolean(
        "Print ProClima logo",
        help="The “pro clima” logo indicates an item for which the "
        "surcharge for carbon-neutral shipping has been paid and a "
        "contract to that effect has been signed. For Letters with "
        "barcode (BMB) domestic, the ProClima logo is printed "
        "automatically (at no additional charge)",
    )
    postlogistics_license_id = fields.Many2one(
        comodel_name="postlogistics.license",
        string="Franking License",
    )
    zpl_patch_string = fields.Char(
        string="ZPL Patch String", default="^XA^CW0,E:TT0003M_.TTF^XZ^XA^CI28"
    )

    @api.model
    def _default_postlogistics_default_package_type_id(self):
        return self.env.ref(
            "delivery_postlogistics.postlogistics_default_package_type",
            raise_if_not_found=False,
        )

    @api.onchange("prod_environment")
    def onchange_prod_environment(self):
        """
        Auto change the end point url following the environment
        - Test: https://wedecint.post.ch/
        - Prod: https://wedec.post.ch/
        """
        for carrier in self:
            if carrier.prod_environment:
                carrier.postlogistics_endpoint_url = "https://wedec.post.ch/"
            else:
                carrier.postlogistics_endpoint_url = "https://wedecint.post.ch/"

    def _postlogistics_get_default_custom_package_code(self):
        # Used while changing the carrier on the stock.package.type Form
        if package_type := self.postlogistics_default_package_type_id:
            return ",".join(package_type._get_shipper_package_code_list())
        # Ultimate fallback
        return "ECO"

    def postlogistics_get_tracking_link(self, picking):
        return (
            "https://service.post.ch/EasyTrack/"
            f"submitParcelData.do?formattedParcelCodes={picking.carrier_tracking_ref}"
        )

    def postlogistics_cancel_shipment(self, pickings):
        raise UserError(self.env._("This feature is under development"))

    def postlogistics_rate_shipment(self, order):
        self.ensure_one()
        delivery_product_price = self.product_id and self.product_id.lst_price or 0
        return {
            "success": True,
            "price": delivery_product_price,
            "error_message": False,
            "warning_message": False,
        }

    def postlogistics_send_shipping(self, pickings):
        """
        It will generate the labels for all the packages of the picking.
        Packages are mandatory in this case
        """
        for picking in pickings:
            carrier = picking.carrier_id
            move_lines = picking.move_line_ids.filtered(
                lambda s: not (s.package_id or s.result_package_id)
            )
            if move_lines:
                default_packaging = carrier.postlogistics_default_package_type_id
                package = self.env["stock.quant.package"].create(
                    [{"package_type_id": default_packaging.id}]
                )
                move_lines.write({"result_package_id": package.id})
            picking.generate_postlogistics_shipping_labels()

        return [{"exact_price": False, "tracking_number": False}]

    def verify_credentials(self):
        if not PostlogisticsWebService.get_access_token(self):
            # Error has already been risen
            return
        message = {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Validated"),
                "message": self.env._("The credential is valid."),
                "sticky": False,
            },
        }
        return message

    def _compute_can_generate_return(self):
        res = super()._compute_can_generate_return()
        for carrier in self:
            if carrier.delivery_type == "postlogistics":
                carrier.can_generate_return = True
        return res

    def postlogistics_get_return_label(
        self, picking, tracking_number=None, origin_date=None
    ):
        return self.postlogistics_send_shipping(picking)
