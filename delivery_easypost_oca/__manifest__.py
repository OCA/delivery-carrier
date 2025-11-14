{
    "name": "Easypost Shipping OCA",
    "version": "16.0.1.0.0",
    "summary": """ OCA Delivery Easypost """,
    "author": "Binhex, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "category": "Inventory/Delivery",
    "depends": [
        "delivery",
        "mail",
    ],
    "data": [
        "views/delivery_carrier_views.xml",
        "views/stock_package_type.xml",
    ],
    "external_dependencies": {"python": ["easypost==7.15.0"]},
    "installable": True,
    "license": "AGPL-3",
}
