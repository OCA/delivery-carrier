# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from openupgradelib import openupgrade


_field_renames = [
    ("res.company", "res_company",
     "postlogistics_default_label_layout", "postlogistics_label_layout"),
    ("res.company", "res_company",
     "postlogistics_default_output_format", "postlogistics_output_format"),
    ("res.company", "res_company",
     "postlogistics_default_resolution", "postlogistics_resolution"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
