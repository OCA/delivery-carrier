from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"

    use_dhl_parcel_de_shipping_provider = fields.Boolean(
        copy=False,
        string="Use DHL Parcel DE Shipping Provider.?",
        default=False,
    )
    dhl_shipping_domain = fields.Char(
        string="Domain", copy=False, default="https://api-sandbox.dhl.com"
    )
    dhl_shipping_endpoint = fields.Char(
        string="Endpoint", copy=False, default="/parcel/de/shipping/v2/orders"
    )

    dhl_shipping_userid = fields.Char(
        "DHL UserId",
        copy=False,
    )
    dhl_shipping_password = fields.Char(
        "DHL Password",
        copy=False,
        help=(
            "When use the sandbox account developer portal password "
            "use to as the password.When use the live account application token use to as the password."
        ),
    )
    dhl_shipping_dhl_api_key = fields.Char(
        "DHL API Key",
        copy=False,
        help="Obtained via Get Access! (app creation) and manually approved by DHL.",
    )
    dhl_shipping_url = fields.Char(compute="_compute_dhl_shipping_url", store=True)

    @api.depends("dhl_shipping_domain", "dhl_shipping_endpoint")
    def _compute_dhl_shipping_url(self):
        for record in self:
            if record.dhl_shipping_domain and record.dhl_shipping_endpoint:
                record.dhl_shipping_url = (
                    record.dhl_shipping_domain + record.dhl_shipping_endpoint
                )
            else:
                record.dhl_shipping_url = False
