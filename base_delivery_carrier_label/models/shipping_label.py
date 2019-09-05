# Copyright 2013-2016 Camptocamp SA
# Copyright 2014 Akretion <http://www.akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ShippingLabel(models.Model):
    """ Child class of ir attachment to identify which are labels """

    _name = 'shipping.label'
    _inherits = {'ir.attachment': 'attachment_id'}
    _description = "Shipping Label"

    file_type = fields.Char(
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
