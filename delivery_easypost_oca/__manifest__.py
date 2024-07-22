{
    "name": "Easypost Shipping OCA",
    "version": "14.0.1.0.0",
    "summary": """ OCA Delivery Easypost """,
    "author": "Binhex",
    "website": "https://binhex.cloud",
    "category": "Inventory/Delivery",
    "depends": [
        "delivery",
        "mail",
    ],
    "data": [
        "views/delivery_carrier_views.xml",
        "security/ir.model.access.csv",
        "views/product_packaging_views.xml",
        "views/easypost_oca_webhook_views.xml",
    ],
    "external_dependencies": {"python": ["easypost"]},
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
