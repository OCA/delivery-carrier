# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Convert current ZIP field values to ZIP entries"""
    env = api.Environment(cr, SUPERUSER_ID, dict())
    carriers = (
        env["delivery.carrier"]
        .with_context(
            show_children_carriers=True  # compatibility with delivery_multi_destination
        )
        .search(["|", ("zip_from", "!=", False), ("zip_to", "!=", False)])
    )
    for carrier in carriers:
        carrier.write({"zip_from": carrier.zip_from, "zip_to": carrier.zip_to})
    env.cr.execute("UPDATE delivery_carrier SET zip_from=NULL, zip_to=NULL")
