# Copyright 2024 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models
from odoo.osv.expression import AND


class ChooseDeliveryPackage(models.TransientModel):

    _inherit = "choose.delivery.package"

    @api.depends("picking_id.picking_type_id.authorized_package_type_cateogory_ids")
    def _compute_package_type_domain(self):
        res = super()._compute_package_type_domain()
        for wizard in self:
            authorized_category_ids = (
                wizard.picking_id.picking_type_id.authorized_package_type_cateogory_ids
            )
            if authorized_category_ids:
                domain = wizard.package_type_domain
                domain = AND(
                    [domain, [("category_id", "in", authorized_category_ids.ids)]]
                )
                wizard.package_type_domain = domain
        return res
