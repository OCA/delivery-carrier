# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models

try:
    from roulier.carriers.dpd_fr.schema import Format
except ImportError:
    Format = None


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    dpd_fr_customer_country = fields.Char(string="DPD Customer Country")
    dpd_fr_customer_id = fields.Char(string="DPD Customer ID")
    dpd_fr_agency_id = fields.Char(string="DPD Agency ID")
    dpd_fr_file_format = fields.Selection(
        (
            [(format.value, format.value) for format in Format]
            if Format
            else [("ZPL", "ZPL"), ("PDF", "PDF")]
        ),
        string="DPD file format",
    )
