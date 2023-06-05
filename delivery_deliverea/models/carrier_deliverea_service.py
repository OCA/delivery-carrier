# © 2023 - FactorLibre - Oscar Indias <oscar.indias@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class CarrierDelivereaService(models.Model):
    _name = "carrier.deliverea.service"

    name = fields.Char()
    description = fields.Char()
    deliverea_parameters = fields.Many2many(comodel_name="carrier.deliverea.parameter")
    carrier_code = fields.Char()
    deliverea_distribution_center_id = fields.Many2one(
        comodel_name="deliverea.distribution.center",
        string="Deliverea Distribution Center",
    )
    code = fields.Char(string="Deliverea service code", required=True)
    carrier_id = fields.One2many(
        comodel_name="delivery.carrier",
        inverse_name="deliverea_carrier_service_id",
    )
    active = fields.Boolean(default=True)
