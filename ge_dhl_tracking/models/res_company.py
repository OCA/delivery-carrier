from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    use_dhl_tracking_de_shipping_provider = fields.Boolean(
        copy=False,
        string="Are You Use DHL Parcel DE Shipping Provider.?",
        help="If use DHL Parcel DE shipping provider than value set TRUE.",
        default=False,
    )
    dhl_tracking_parcel_de_api_url = fields.Char(
        string="API URL", copy=False, default="https://api-sandbox.dhl.com"
    )
    dhl_tracking_userid = fields.Char(
        "DHL UserId",
        copy=False,
        help=(
            "When use the sandbox account developer id use as the userId."
            "When use the live account application id use as the userId."
        ),
    )
    dhl_tracking_password = fields.Char(
        "DHL Password",
        copy=False,
        help=(
            "When use the sandbox account developer portal password "
            "use to as the password.When use the live account application token "
            "use to as the password."
        ),
    )
    dhl_tracking_dhl_api_key = fields.Char(
        "DHL API Key",
        copy=False,
        help=("Obtained via Get Access! (app creation) and manually approved by DHL."),
    )
    dhl_tracking_dhl_api_secret = fields.Char(
        "DHL API Secret",
        copy=False,
        help=("Obtained via Get Access! (app creation) and manually approved by DHL."),
    )
    dhl_tracking_domain = fields.Char(
        help="Domain for test environment: https://api-sandbox.dhl.com"
    )
    dhl_tracking_endpoint = fields.Char(
        help="endpoint for test environment: /parcel/de/tracking/v0/shipments"
    )
    dhl_tracking_url = fields.Char(compute="_compute_dhl_tracking_url", store=True)

    @api.depends("dhl_tracking_domain", "dhl_tracking_endpoint")
    def _compute_dhl_tracking_url(self):
        for record in self:
            if record.dhl_tracking_domain and record.dhl_tracking_endpoint:
                record.dhl_tracking_url = (
                    record.dhl_tracking_domain + record.dhl_tracking_endpoint
                )
            else:
                record.dhl_tracking_url = False
