# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import fields, models


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    resource_type = fields.Selection(
        selection_add=[("carrier", "Carrier")],
        ondelete={"carrier": "set default"},
    )
