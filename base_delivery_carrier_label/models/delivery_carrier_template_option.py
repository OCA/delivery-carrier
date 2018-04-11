# Copyright 2012 Akretion <http://www.akretion.com>.
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrierTemplateOption(models.Model):
    """ Available options for a carrier (partner) """
    _name = 'delivery.carrier.template.option'
    _description = 'Delivery carrier template option'

    partner_id = fields.Many2one(comodel_name='res.partner',
                                 string='Partner Carrier')
    name = fields.Char(readonly=True)
    code = fields.Char(readonly=True)
    description = fields.Char(
        readonly=True,
        help="Allow to define a more complete description "
             "than in the name field."
    )
