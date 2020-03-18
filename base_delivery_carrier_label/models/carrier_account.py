# Copyright 2014-TODAY Florian da Costa Akretion <http://www.akretion.com>.
# Copyright 2014 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class CarrierAccount(models.Model):
    _name = "carrier.account"
    _description = "Base account datas"

    @api.model
    def _selection_file_format(self):
        """ To inherit to add label file types"""
        return [("PDF", "PDF"), ("ZPL", "ZPL"), ("XML", "XML")]

    name = fields.Char(required=True)
    delivery_type = fields.Selection(
        selection=lambda self: self.env["delivery.carrier"]
        ._fields["delivery_type"]
        .selection,
        help="This field may be used to link an account to a carrier",
    )
    account = fields.Char(string="Account Number", required=True)
    password = fields.Char(string="Account Password", required=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    file_format = fields.Selection(
        selection="_selection_file_format",
        string="File Format",
        help="Default format of the carrier's label you want to print",
    )
