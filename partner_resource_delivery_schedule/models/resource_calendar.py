# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    is_delivery_schedule = fields.Boolean()

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        res = super().check_access_rights(operation, raise_exception=raise_exception)
        return res

    def check_access_rule(self, operation):
        res = super().check_access_rule(operation)
        return res
