# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import api, models


class OnboardingStep(models.Model):
    _inherit = "onboarding.onboarding.step"

    @api.model
    def action_open_sendcloud_onboarding_integration(self):
        """Called by onboarding panel."""
        action_name = (
            "delivery_sendcloud_oca.action_sendcloud_onboarding_integration_wizard"
        )
        return self.env.ref(action_name).read()[0]

    @api.model
    def action_sendcloud_onboarding_sync(self):
        """Called by onboarding panel."""
        action_name = "delivery_sendcloud_oca.action_sendcloud_onboarding_sync_wizard"
        return self.env.ref(action_name).read()[0]

    @api.model
    def action_open_sendcloud_onboarding_warehouse_address(self):
        """Called by onboarding panel."""
        action_name = (
            "delivery_sendcloud_oca.action_sendcloud_onboarding_warehouse_wizard"
        )
        return self.env.ref(action_name).read()[0]
