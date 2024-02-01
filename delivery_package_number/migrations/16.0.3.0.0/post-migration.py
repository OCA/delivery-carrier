# Copyright 2023 Studio73 - Ferran Mora
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    ptypes = env["stock.picking.type"].search([("print_label", "=", True)])
    if ptypes:
        ptypes.write({"print_label_on_validate": True})
