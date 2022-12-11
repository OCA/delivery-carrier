# Copyright 2014-TODAY Florian da Costa Akretion <http://www.akretion.com>.
# Copyright 2014 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class CarrierAccount(models.Model):
    _name = "carrier.account"
    _description = "Base account datas"
    _order = "sequence"

    @api.model
    def _get_selection_delivery_type(self):
        return self.env["delivery.carrier"].fields_get(allfields=["delivery_type"])[
            "delivery_type"
        ]["selection"]

    name = fields.Char(required=True)
    sequence = fields.Integer()
    delivery_type = fields.Selection(
        selection="_get_selection_delivery_type",
        help="This field may be used to link an account to a carrier",
    )
    carrier_ids = fields.Many2many(
        "delivery.carrier",
        "delivery_carrier_account_rel",
        "account_id",
        "carrier_id",
        string="Carriers",
        help=(
            "This optional field may be used if the carrier account changes depending "
            "on delivery methods belonging to a same carrier (same delivery type)"
        ),
    )
    account = fields.Char(string="Account Number", required=True)
    password = fields.Char(string="Account Password", required=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
