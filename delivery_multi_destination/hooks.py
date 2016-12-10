# -*- coding: utf-8 -*-
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, SUPERUSER_ID
try:
    from openupgradelib import openupgrade
except ImportError:
    openupgrade = False


def migrate_from_v8(cr):
    """Reconvert delivery carriers that were the grids from the same
    v8 carrier again on childs with this new structure.
    """
    cr.execute(
        """
        SELECT COUNT({0}), {0}
        FROM carrier_delivery
        GROUP BY {0}
        """.format(openupgrade.get_legacy_name('carrier_id'))
    )
    rows = cr.fetchall()
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        carrier_obj = env['delivery.carrier']
        for count, old_carrier_id in rows:
            if count <= 1:
                continue
            # Get children ids
            cr.execute(
                """
                SELECT id
                FROM carrier_delivery
                WHERE {0} = %s
                """.format(openupgrade.get_legacy_name('carrier_id')),
                (old_carrier_id, )
            )
            child_ids = [x[0] for x in cr.fetchall()]
            # Get old carrier data
            cr.execute(
                """
                SELECT name, partner_id
                FROM carrier_delivery
                WHERE {0} = %s
                """.format(openupgrade.get_legacy_name('carrier_id')),
                (old_carrier_id, )
            )
            old_carrier_vals = cr.fetchone()
            # Create new carrier and put the rest of the carriers as children
            carrier = carrier_obj.create({
                'name': old_carrier_vals[0],
                'partner_id': old_carrier_vals[1],
                'destination_type': 'multi',
            })
            cr.execute(
                """
                UPDATE carrier_delivery
                SET parent_id = %s
                WHERE ids = %s
                """, (carrier.id, tuple(child_ids))
            )


def post_init_hook(cr, registry):  # pragma: no cover
    if openupgrade and openupgrade.column_exists(
            'delivery_carrier', openupgrade.get_legacy_name('carrier_id')):
        migrate_from_v8(cr)


def uninstall_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        act_window = env.ref('delivery.action_delivery_carrier_form')
        if act_window:
            act_window.domain = False
