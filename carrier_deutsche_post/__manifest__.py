{
    'name': "Delivery Carrier Deutsche Post",
    'category': 'Website',
    'version': '12.0.1.0.0',
    'depends': [
        'stock',
        'delivery',
        'base_delivery_carrier_label',
    ],
    'data': [
        'views/delivery_views.xml',
        'views/carrier_account_views.xml',
        'views/stock_views.xml',
        'views/country_views.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/country_data.xml',
        'views/carrier_deutsche_post.xml',
    ],
    'qweb': [
        "static/src/xml/picking.xml",
    ],
    'author': "Nitrokey GmbH, Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': "https://github.com/OCA/carrier_deutsche_post",
}
