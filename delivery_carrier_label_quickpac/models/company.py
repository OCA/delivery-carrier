# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    quickpac_username = fields.Char('Username')
    quickpac_password = fields.Char('Password')
    quickpac_franking_license = fields.Char("Franking License")
    quickpac_sending_id = fields.Char("Sending ID")
    quickpac_label_layout = fields.Many2one(
        'delivery.carrier.template.option',
        'Default label layout',
        domain=[('quickpac_type', '=', 'label_layout')],
    )
    quickpac_output_format = fields.Many2one(
        'delivery.carrier.template.option',
        'Default output format',
        domain=[('quickpac_type', '=', 'output_format')],
    )
    quickpac_resolution = fields.Many2one(
        'delivery.carrier.template.option',
        'Default resolution',
        domain=[('quickpac_type', '=', 'resolution')],
    )
    quickpac_tracking_format = fields.Selection(
        [
            ('quickpac', "Use default quickpac tracking numbers"),
            ('picking_num', 'Use picking number with pack counter'),
        ],
        "Tracking number format",
        default='quickpac',
    )
    quickpac_logo = fields.Binary(
        string='Company Logo on Post labels',
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
    quickpac_office = fields.Char(
        string='Domicile Post office',
        help="Post office which will receive the shipped goods",
    )
    quickpac_tracking_url = fields.Char(
        "Tracking URL",
        default="https://quickpac.ch/{lang}/tracking/{number}",
        help="Available variables to configure: \n \
              {lang} = the lang to display (de, en, fr, it) \n \
              {number} = the tracking number (i.e. 440010370000000034)""")
