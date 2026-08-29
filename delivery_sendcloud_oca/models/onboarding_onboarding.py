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

    @api.model
    def get_sendcloud_onboarding_data(self):
        onboarding_data = {}
        if self.env.user._is_admin():
            sendcloud_onboarding = self.env.ref(
                "delivery_sendcloud_oca.onboarding_onboarding_sendcloud"
            )
            if sendcloud_onboarding:
                progress = sendcloud_onboarding._search_or_create_progress()
                if not progress.is_onboarding_closed:
                    onboarding_data["onboarding_state"] = progress.onboarding_state
                    ob = progress.onboarding_id
                    ob_vals = ob.with_company(
                        progress.company_id
                    )._prepare_rendering_values()
                    steps = []
                    for step in sendcloud_onboarding.step_ids:
                        steps.append(
                            {
                                "id": step.id,
                                "title": step.title,
                                "description": step.description,
                                "state": ob_vals["state"][step.id],
                                "action": step.panel_step_open_action_name,
                                "done_icon": step.done_icon,
                                "button_text": step.button_text,
                                "done_text": step.done_text,
                                "step_image_alt": step.step_image_alt,
                            }
                        )
                    onboarding_data["steps"] = steps
        return onboarding_data
