# -*- coding: utf-8 -*-
# Copyright 2018 Halltic eSolutions S.L.
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# This project is based on connector-magneto, developed by Camptocamp SA

from odoo.addons.connector.event import Event

on_picking_out_done = Event()
"""
``on_picking_out_done`` is fired when an outgoing picking has been
marked as done.

Listeners should take the following arguments:

 * session: `connector.session.ConnectorSession` object
 * model_name: name of the model
 * record_id: id of the record
 * type: 'partial' or 'complete' depending on the picking done
"""

on_tracking_number_added = Event()
"""
``on_tracking_number_added`` is fired when a picking has been marked as
 done and a tracking number has been added to it (write).

Listeners should take the following arguments:

 * session: `connector.session.ConnectorSession` object
 * model_name: name of the model
 * record_id: id of the record
"""

on_product_price_changed = Event()
"""
``on_product_price_changed`` is fired when the price of a product is
changed. Specifically, it is fired when one of the products' fields used
in the sale pricelists are modified.

There is no guarantee that's the price actually changed,
because it depends on the pricelists.

 * session: `connector.session.ConnectorSession` object
 * model_name: name of the model
 * record_id: id of the record

"""
