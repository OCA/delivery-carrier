# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "Transsmart Integration",
    'summary': """Transsmart Integration for Odoo""",
    'author': "Therp B.V, 1200WD B.V, Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'category': 'Warehouse',
    'version': '8.0.0.1.0',
    'depends': [
        'stock',
        'delivery',
        'product_harmonized_system',
    ],
    'data': [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/transsmart_config_settings.xml",
        "views/res_company.xml",
        "views/service_level_other.xml",
        "views/service_level_time.xml",
        "views/cost_center.xml",
        "views/res_partner.xml",
        "views/stock_picking.xml",
        "views/product_template.xml",
        "views/booking_profile.xml",
        "wizards/stock_transfer_details.xml",
    ],
    'application': True,
    'external_dependencies': {
        'python': ['mock', 'transsmart']
    },
}
