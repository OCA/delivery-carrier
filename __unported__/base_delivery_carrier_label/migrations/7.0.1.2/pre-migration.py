# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: David BEAL
#    Copyright 2014 Akretion
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


def migrate(cr, version):
    if not version:
        return

    queries = [
        # build new fields
        """ALTER TABLE delivery_carrier_option
        ADD COLUMN mandatory BOOLEAN,
        ADD COLUMN by_default BOOLEAN;""",
        # move datas to new fields
        """UPDATE delivery_carrier_option
        SET mandatory = 't' WHERE state='mandatory';""",
        """UPDATE delivery_carrier_option
        SET by_default = 't' WHERE state='default_option';""",
        # Delete old column
        "ALTER TABLE delivery_carrier_option DROP COLUMN state;"
    ]

    for query in queries:
        cr.execute(query)
