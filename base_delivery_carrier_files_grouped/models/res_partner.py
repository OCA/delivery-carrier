# Copyright 2020 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    one_delivery_by_picking = fields.Boolean('One Delivery by Picking',
                                             default=True)
