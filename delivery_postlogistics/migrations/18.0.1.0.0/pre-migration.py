# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


MODEL_TO_RENAMED_FIELDS = {
    "res.partner": [
        ("postlogistics_option_ids", "delivery_carrier_template_option_ids"),
    ],
    "delivery.carrier.template.option": [
        ("postlogistics_type", "type"),
    ],
}


def _migrate_models(env):
    xmlids_spec = [
        (
            "delivery_postlogistics.postlogistics_delivery_carrier_template_option",
            "delivery_carrier_option.delivery_carrier_template_option",
        )
    ]
    openupgrade.rename_xmlids(env.cr, xmlids_spec)


def _rename_models(env):
    models_spec = [
        (
            "postlogistics.delivery.carrier.template.option",
            "delivery.carrier.template.option",
        )
    ]
    openupgrade.rename_models(env.cr, models_spec)


def _rename_fields(env):
    openupgrade.rename_fields(
        env,
        [
            (
                model_name,
                env[model_name]._table,
                field_spec[0],
                field_spec[1],
            )
            for model_name, field_specs in MODEL_TO_RENAMED_FIELDS.items()
            for field_spec in field_specs
        ],
    )


def migrate(env, version):
    _rename_models(env)
    _migrate_models(env)
    _rename_fields(env)
