from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    use_dhl_return_de_shipping_provider = fields.Boolean(
        copy=False,
        string="Are You Use DHL Parcel DE Shipping Provider.?",
        help="If use DHL Parcel DE shipping provider than value set TRUE.",
        default=False,
    )
    dhl_return_userid = fields.Char(
        "DHL UserId",
        copy=False,
        help=(
            "When use the sandbox account developer id use as the userId."
            "When use the live account application id use as the userId."
            "For the test environment it's: 2222222222_customer"
        ),
    )
    dhl_return_password = fields.Char(
        "DHL Password",
        copy=False,
        help=(
            "When use the sandbox account developer portal password use to as the password."
            "When use the live account application token use to as the password."
            "For the test environment it's: uBQbZ62!ZiBiVVbhc"
        ),
    )
    dhl_return_dhl_api_key = fields.Char(
        "DHL API Key",
        copy=False,
        help="Obtained via Get Access! (app creation) and manually approved by DHL.",
    )
    dhl_return_dhl_api_secret = fields.Char(
        "DHL API Secret",
        copy=False,
        help="Obtained via Get Access! (app creation) and manually approved by DHL.",
    )
    dhl_return_domain = fields.Char(
        help="Domain for test environment: https://api-sandbox.dhl.com"
    )
    dhl_return_endpoint = fields.Char(
        help="endpoint for test environment: /parcel/de/shipping/returns/v1/orders"
    )
    dhl_return_url = fields.Char(compute="_compute_dhl_return_url")

    dhl_return_receiverId = fields.Char(default="deu")

    @api.depends("dhl_return_domain", "dhl_return_endpoint")
    def _compute_dhl_return_url(self):
        for record in self:

            if record.dhl_return_domain and record.dhl_return_endpoint:
                record.dhl_return_url = (
                    record.dhl_return_domain + record.dhl_return_endpoint
                )
            else:
                record.dhl_return_url = False
