# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.delivery_ups_oca.hooks import create_declared_value_columns


def migrate(cr, version):
    if not version:
        return
    create_declared_value_columns(cr)
