#   @author: David BEAL <david.beal@akretion.com>
#   @author: Sebastien BEAU <sebastien.beau@akretion.com>
#   @author: Benoit GUILLOT <benoit.guillot@akretion.com>
#   @author: Chafique DELLI <chafique.delli@akretion.com>
#   @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class DepositSlip(models.Model):
    _name = "deposit.slip"
    _description = "Deposit Slip"
    _order = "id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    @api.depends("picking_ids")
    def _compute_weight(self):
        weight = 0.0
        for picking in self.picking_ids:
            weight += picking.shipping_weight
        self.weight = weight

    name = fields.Char(
        readonly=True, states={"draft": [("readonly", False)]}, default="/", copy=False
    )
    delivery_type = fields.Selection(
        selection=lambda self: self.env["delivery.carrier"]
        ._fields["delivery_type"]
        .selection
    )
    picking_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="deposit_slip_id",
        string="Pickings",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        string="Status",
        readonly=True,
        default="draft",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    weight = fields.Float(
        string="Total Weight",
        compute="_compute_weight",
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique(name, company_id)",
            "'Deposit Slip' name must be unique per company!",
        )
    ]

    @api.model
    def create(self, vals=None):
        if vals is None:
            vals = {}
        if vals.get("name", "/") == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code("delivery.deposit")
        return super().create(vals)

    def create_edi_file(self):
        """
        Override this method for the proper carrier
        """
        return True

    def validate_deposit(self):
        self.create_edi_file()
        self.write({"state": "done"})
        return True
