# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def uninstall_hook(env):
    # Remove custom data (domain + context)
    act_window = env.ref("delivery.action_delivery_carrier_form")
    act_window.write(
        {
            "domain": [],
            "context": {"search_default_group_by_provider": True},
        }
    )
