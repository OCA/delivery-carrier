# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class Onboarding(models.Model):
    _inherit = "onboarding.onboarding"

    # Sendcloud Onboarding
    @api.model
    def action_close_sendcloud_onboarding(self):
        self.action_close_panel(
            "delivery_sendcloud_oca.onboarding_onboarding_sendcloud"
        )
