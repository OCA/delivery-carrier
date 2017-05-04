# -*- coding: utf-8 -*-
# Copyright 2014-TODAY Florian da Costa Akretion <http://www.akretion.com>.
# Copyright 2014 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api


class CarrierAccount(models.Model):
    _name = 'carrier.account'
    _description = 'Base account datas'

    @api.model
    def _get_carrier_type(self):
        """ To inherit to add carrier type like Chronopost, Postlogistics..."""
        return []

    @api.model
    def _get_file_format(self):
        """ To inherit to add label file types"""
        return [('PDF', 'PDF'),
                ('ZPL', 'ZPL'),
                ('XML', 'XML')]

    name = fields.Char(required=True)
    account = fields.Char(string='Account Number', required=True)
    password = fields.Char(string='Account Password', required=True)
    file_format = fields.Selection(
        selection='_get_file_format',
        string='File Format',
        help="Default format of the carrier's label you want to print"
    )
    type = fields.Selection(
        selection='_get_carrier_type',
        required=True,
        help="In case of several carriers, help to know which "
             "account belong to which carrier",
    )
