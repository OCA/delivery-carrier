# Copyright 2013-2019 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

from .company import ResCompany

_logger = logging.getLogger(__name__)


class QuickpacConfigSettings(models.TransientModel):
    _name = 'res.config.settings'
    _inherit = ['res.config.settings', 'abstract.config.settings']

    # AbstractConfigSettings attribute
    _prefix = 'quickpac_'
    _companyObject = ResCompany
