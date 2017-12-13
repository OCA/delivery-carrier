# coding: utf-8
# © 2016 David BEAL @ Akretion <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class DeliveryCarrierTemplateOption(models.Model):
    """ Available options for a carrier (partner) """
    _inherit = 'delivery.carrier.template.option'

    name = fields.Char(translate=True)
