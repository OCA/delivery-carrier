# © 2016 David BEAL @ Akretion <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class DeliveryCarrierTemplateOption(models.Model):
    _inherit = "delivery.carrier.template.option"

    name = fields.Char(translate=True)
