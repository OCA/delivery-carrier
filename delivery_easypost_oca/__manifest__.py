{
    "name": "Easypost Shipping OCA",
    "version": "14.0.1.0.5",
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
        "views/product_packaging_views.xml",
    ],
    "external_dependencies": {"python": ["easypost", "easypost==7.15.0"]},
    "installable": True,
    "license": "AGPL-3",
}
