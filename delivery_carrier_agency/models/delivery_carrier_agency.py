# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrierAgency(models.Model):
    _name = "delivery.carrier.agency"
    _description = "Carrier Agency"
    _order = "sequence, id"

    name = fields.Char(required=True)
    external_reference = fields.Char(help="Reference or code supplied by the carrier")
    delivery_type = fields.Selection(
        selection=lambda self: self.env["delivery.carrier"]
        ._fields["delivery_type"]
        .selection,
        required=True,
    )
    carrier_ids = fields.Many2many(
        "delivery.carrier",
        "delivery_carrier_agency_rel",
        "agency_id",
        "carrier_id",
        string="Carriers",
        help=(
            "This field may be used to link an account to specific delivery methods"
            " It may be usefull to find an account with more precision than with "
            "only the delivery type"
        ),
    )
    partner_id = fields.Many2one("res.partner", string="Address")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouses")
    sequence = fields.Integer()
