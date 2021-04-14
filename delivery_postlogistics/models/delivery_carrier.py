# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):
    """ Add service group """

    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("postlogistics", "Post logistics")]
    )
    postlogistics_default_packaging_id = fields.Many2one(
        "product.packaging", domain=[("package_carrier_type", "=", "postlogistics")]
    )

    postlogistics_endpoint_url = fields.Char(
        string="Endpoint URL", default="https://wedecint.post.ch/", required=True,
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
        comodel_name="postlogistics.delivery.carrier.template.option",
        string="Label layout",
        domain=[("postlogistics_type", "=", "label_layout")],
    )
    postlogistics_output_format = fields.Many2one(
        comodel_name="postlogistics.delivery.carrier.template.option",
        string="Output format",
        domain=[("postlogistics_type", "=", "output_format")],
    )
    postlogistics_resolution = fields.Many2one(
        comodel_name="postlogistics.delivery.carrier.template.option",
        string="Resolution",
        domain=[("postlogistics_type", "=", "resolution")],
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
        comodel_name="postlogistics.license", string="Franking License",
    )
    zpl_patch_string = fields.Char(
        string="ZPL Patch String", default="^XA^CW0,E:TT0003M_.TTF^XZ^XA^CI28"
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

    def postlogistics_get_tracking_link(self, picking):
        return (
            "https://service.post.ch/EasyTrack/"
            "submitParcelData.do?formattedParcelCodes=%s" % picking.carrier_tracking_ref
        )

    def postlogistics_cancel_shipment(self, pickings):
        raise UserError(_("This feature is under development"))

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
        for pick in pickings:
            pick._set_a_default_package()
            pick._generate_postlogistics_label()

        return [{"exact_price": False, "tracking_number": False}]
