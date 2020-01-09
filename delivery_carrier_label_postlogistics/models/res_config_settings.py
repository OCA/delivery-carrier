# Copyright 2013-2019 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

from . company import ResCompany

_logger = logging.getLogger(__name__)


class PostlogisticsConfigSettings(models.TransientModel):
    _name = 'res.config.settings'
    _inherit = ['res.config.settings', 'abstract.config.settings']

    # AbstractConfigSettings attribute
    _prefix = 'postlogistics_'
    _companyObject = ResCompany

    tracking_format = fields.Selection(
        related='company_id.postlogistics_tracking_format',
        selection=[
            ('postlogistics', "Use default postlogistics tracking numbers"
             ),
            ('picking_num', 'Use picking number with pack counter')],
        string="Tracking number format", type='selection',
        help="Allows you to define how the ItemNumber (the last 8 digits) "
             "of the tracking number will be generated:\n"
             "- Default postlogistics numbers: The webservice generates it"
             " for you.\n"
             "- Picking number with pack counter: Generate it using the "
             "digits of picking name and add the pack number. 2 digits for"
             "pack number and 6 digits for picking number. (eg. 07000042 "
             "for picking 42 and 7th pack")
    proclima_logo = fields.Boolean(
        related='company_id.postlogistics_proclima_logo',
        help="The “pro clima” logo indicates an item for which the "
             "surcharge for carbon-neutral shipping has been paid and a "
             "contract to that effect has been signed. For Letters with "
             "barcode (BMB) domestic, the ProClima logo is printed "
             "automatically (at no additional charge)"
    )
