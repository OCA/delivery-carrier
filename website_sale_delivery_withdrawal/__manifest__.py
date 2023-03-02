# -*- coding: utf-8 -*-
{
    'name': "website_sale_delivery_withdrawal",
    'summary': """ Let's choose withdrawal point on your ecommerce """,
    'description': """
        This module allow your customer to choose a Withdrawal Point and use it as shipping address.
    """,
    'category': 'Website/Website',
    'version': '0.1',
    'depends': ['website_sale_delivery', 'withdrawal_methods'],
    'assets': {
        'web.assets_frontend': [
            'website_sale_delivery_withdrawal/static/src/js/website_sale_delivery_withdrawal.js',
            'website_sale_delivery_withdrawal/static/src/css/website_sale_delivery_withdrawal.css'
        ],
    },
    'license': 'LGPL-3',
    'auto_install': True,
}
