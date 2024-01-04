# Copyright (C) 2014 - Today: Akretion (http://www.akretion.com)
# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author Aymeric Lecomte <aymeric.lecomte@akretion.com>
# @author David BEAL <david.beal@akretion.com>
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.fields import first


class ResPartner(models.Model):
    _inherit = "res.partner"
    _rec_names_search = ["dropoff_site_id"]

    dropoff_site_ids = fields.One2many(
        comodel_name="dropoff.site", inverse_name="partner_id"
    )

    dropoff_site_id = fields.Many2one(
        comodel_name="dropoff.site",
        compute="_compute_multi_dropoff_site",
        string="Drop-off Site",
        store=True,
    )

    dropoff_site_carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        compute="_compute_multi_dropoff_site",
        string="Carrier of the Drop-off Site",
        store=True,
    )

    is_dropoff_site = fields.Boolean(
        compute="_compute_multi_dropoff_site",
        string="Is Drop-off Site",
        store=True,
    )

    @api.depends("dropoff_site_ids.partner_id", "dropoff_site_ids.carrier_id")
    def _compute_multi_dropoff_site(self):
        for partner in self:
            partner.dropoff_site_id = partner.dropoff_site_ids and first(
                partner.dropoff_site_ids
            )
            partner.dropoff_site_carrier_id = partner.dropoff_site_id.carrier_id
            partner.is_dropoff_site = partner.dropoff_site_id

    _sql_constraints = [
        (
            "dropoff_site_id_uniq",
            "unique(dropoff_site_id)",
            "Dropoff Site with the same id already exists : must be unique",
        ),
    ]
