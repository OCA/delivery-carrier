# -*- coding: utf-8 -*-
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, SUPERUSER_ID
try:
    from openupgradelib import openupgrade
except ImportError:
    openupgrade = False


def migrate_from_v8(env):
    """Reconvert delivery carriers that were the grids from the same
    v8 carrier again on children with this new structure.
    """
    cr = env.cr
    old_column = openupgrade.get_legacy_name('carrier_id')
    old_table = openupgrade.get_legacy_name('delivery_carrier')
    cr.execute(
        "SELECT COUNT({0}), {0} FROM delivery_carrier GROUP BY {0}".format(
            old_column,
        )
    )
    rows = cr.fetchall()
    Carrier = env['delivery.carrier']
    for count, old_carrier_id in rows:
        if count <= 1:
            continue
        # Get children ids
        cr.execute(
            "SELECT id FROM delivery_carrier WHERE {} = %s".format(old_column),
            (old_carrier_id, )
        )
        child_ids = [x[0] for x in cr.fetchall()]
        # Get old carrier data
        cr.execute(
            "SELECT name, partner_id FROM {} WHERE id = %s".format(old_table),
            (old_carrier_id, )
        )
        old_carrier_vals = cr.fetchone()
        # Create new carrier and put the rest of the carriers as children
        carrier = Carrier.create({
            'name': old_carrier_vals[0],
            'partner_id': old_carrier_vals[1],
            'destination_type': 'multi',
        })
        cr.execute(
            "UPDATE delivery_carrier SET parent_id = %s WHERE id IN %s",
            (carrier.id, tuple(child_ids))
        )


def post_init_hook(cr, registry):  # pragma: no cover
    if openupgrade and openupgrade.column_exists(
            cr, 'delivery_carrier', openupgrade.get_legacy_name('carrier_id')):
        with api.Environment.manage():
            env = api.Environment(cr, SUPERUSER_ID, {})
            migrate_from_v8(env)


def uninstall_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        act_window = env.ref('delivery.action_delivery_carrier_form')
        if act_window:
            act_window.domain = False
