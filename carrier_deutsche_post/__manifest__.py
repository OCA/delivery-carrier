{
    "name": "Delivery Carrier Deutsche Post",
    "category": "Website",
    "version": "15.0.1.0.0",
    "depends": [
        "stock",
        "delivery",
        "base_delivery_carrier_label",
    ],
    "data": [
        "views/delivery_views.xml",
        "views/carrier_account_views.xml",
        "views/stock_views.xml",
        "views/country_views.xml",
        "security/ir.model.access.csv",
        "data/country_data.xml",
    ],
    "qweb": [
        "static/src/xml/picking.xml",
    ],
    "external_dependencies": {"python": ["inema"]},
    "author": "Nitrokey GmbH, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/delivery-carrier",
    "assets": {
        "web.assets_backend": [
            "carrier_deutsche_post/static/src/js/carrier_deutsche_post.js",
        ],
    },
}
