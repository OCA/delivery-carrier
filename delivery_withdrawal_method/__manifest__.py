{
    "name": "Delivery Withdrawal Methods",
    "summary": "Delivery Withdrawal Methods",
    "author": "Moka Tourisme",
    "website": "https://www.mokatourisme.fr",
    "category": "Others",
    "version": '15.0.0.1.0',
    "license": "AGPL-3",
    "depends": [
        "stock",
        "delivery",
        "hr"
    ],
    "data": [
        'data/withdrawal_data.xml',
        'security/ir.model.access.csv',
        'security/delivery_carrier_security.xml',
        'views/withdrawal_methods.xml',
        'views/withdrawal_working_hour.xml',
        'views/resource_views.xml',
    ],
    'web.assets_backend': [
        'static/src/css/*',
        'static/src/js/withdrawal_points.js'
    ]
}
