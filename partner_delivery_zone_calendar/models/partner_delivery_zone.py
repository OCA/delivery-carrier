# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PartnerDeliveryZone(models.Model):

    _inherit = "partner.delivery.zone"

    calendar_id = fields.Many2one(comodel_name="resource.calendar")
