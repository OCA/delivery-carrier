# -*- coding: utf-8 -*-
# Copyright 2013-2016 Camptocamp SA
# Copyright 2014 Akretion <http://www.akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models


class ShippingLabel(models.Model):
    """ Child class of ir attachment to identify which are labels """

    _name = 'shipping.label'
    _inherits = {'ir.attachment': 'attachment_id'}
    _description = "Shipping Label"

    @api.model
    def _get_file_type_selection(self):
        """ To inherit to add file type """
        return [('pdf', 'PDF')]

    @api.model
    def __get_file_type_selection(self):
        file_types = self._get_file_type_selection()
        file_types = list(set(file_types))
        file_types.sort(key=lambda t: t[0])
        return file_types

    file_type = fields.Selection(
        selection=__get_file_type_selection,
        string='File type',
        default='pdf',
    )
    package_id = fields.Many2one(comodel_name='stock.quant.package',
                                 string='Pack')
    attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachement',
        required=True,
        ondelete='cascade',
    )
