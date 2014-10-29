# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""
Monkey patching Cursor to be able to write file on fs only once
the commit is completed. Thus in case of rollback we won't create
orphan files.
"""

from openerp.sql_db import Cursor

Cursor.transaction_actions = []


def add_transaction_action(cr, callback, *args):
    """ Queue file information to be written after commit """
    cr.transaction_actions.append((cr._cnx, callback, args))

Cursor.add_transaction_action = add_transaction_action


former_commit = Cursor.commit


def commit(self):
    """ Perform an SQL `COMMIT`
    With write of file after commit to ensure it
    is written only after commit. And won't be
    in case of rollback.
    """
    res = former_commit(self)
    to_do = [act for act in self.transaction_actions if act[0] == self._cnx]
    for act in to_do:
            act[1](*act[2])
    return res

Cursor.commit = commit


former_rollback = Cursor.rollback


def rollback(self):
    """ Perform an SQL `ROLLBACK`
    Clean file queue for the rolled back cursor
    """
    to_remove = [index for index, act in enumerate(self.transaction_actions)
                 if act[0] != self._cnx]
    # start at end to avoid recomputing offset
    for index in reversed(to_remove):
        del self.transaction_actions[index]
    return former_rollback(self)

Cursor.rollback = rollback
