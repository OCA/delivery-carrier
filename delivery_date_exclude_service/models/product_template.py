# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    service_affect_delivery_date = fields.Boolean(
        string="Affect Delivery Date",
        help="By default, this service product won't impact the sales order"
        " delivery date computation unless this is flagged.",
    )
