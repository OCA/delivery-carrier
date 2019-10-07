# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class SupplierImportMapper(AbstractComponent):
    _name = 'supplier.import.mapper'
    _inherit = ['base.supplier.connector', 'base.import.mapper']
    _usage = 'import.mapper'


def normalize_datetime(field):
    """Change a invalid date which comes from Supplier, if
    no real date is set to null for correct import to
    OpenERP"""

    def modifier(self, record, to_attr):
        if record[field] == '0000-00-00 00:00:00':
            return None
        return record[field]

    return modifier
