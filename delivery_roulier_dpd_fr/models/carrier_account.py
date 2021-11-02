# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    dpd_fr_soap_customer_country = fields.Char()
    dpd_fr_soap_customer_id = fields.Char()
    dpd_fr_soap_agency_id = fields.Char()
    dpd_fr_soap_file_format = fields.Selection([("ZPL", "ZPL"), ("PDF", "PDF")])
