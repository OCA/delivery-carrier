# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openupgradelib import openupgrade


def _move_postlogistics_delivery_carrier_template_option(cr):
    query = """
        ALTER TABLE delivery_carrier_template_option
        ADD COLUMN IF NOT EXISTS
        old_postlogistics_delivery_carrier_template_option integer
    """
    openupgrade.logged_query(cr, query)
    # Insert data from old model to new
    query = """
        INSERT INTO delivery_carrier_template_option
        (name,type,partner_id,code,old_postlogistics_delivery_carrier_template_option)
            (SELECT name, postlogistics_type, partner_id, code,id
            FROM postlogistics_delivery_carrier_template_option pdcto)
            RETURNING id, old_postlogistics_delivery_carrier_template_option
    """
    openupgrade.logged_query(cr, query)
    openupgrade.merge_models(
        cr,
        "postlogistics.delivery.carrier.template.option",
        "delivery.carrier.template.option",
        "old_postlogistics_delivery_carrier_template_option",
    )
    query = """
        UPDATE ir_model_data
            SET model = 'delivery.carrier.template.option'
            WHERE model = 'postlogistics.delivery.carrier.template.option'
    """


def migrate(cr, version):
    _move_postlogistics_delivery_carrier_template_option(cr)
