# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute(
        """UPDATE delivery_carrier SET cbl_freight_type = 'P'
        WHERE delivery_type = 'cbl'AND cbl_cash_on_delivery IS DISTINCT FROM False"""
    )
