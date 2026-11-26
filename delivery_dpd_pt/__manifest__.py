{
    "name": "Delivery DPD Portugal",
    "summary": "Integrate DPD Portugal shipping operations from Odoo",
    "version": "19.0.1.0.0",
    "category": "Inventory/Delivery",
    "author": "Daniel Reis <dreis.pt@gmail.com>, Odoo Community Association (OCA)",
    "maintainer": "dreispt",
    "website": "https://github.com/OCA/delivery-carrier",
    "license": "AGPL-3",
    "depends": [
        "delivery_carrier_account",
        "delivery_package_number",
        "stock_delivery",
    ],
    "external_dependencies": {"python": ["phonenumbers", "requests"]},
    "data": [
        "views/carrier_account.xml",
        "views/delivery_carrier.xml",
        "views/stock_picking.xml",
    ],
    "installable": True,
    "application": False,
}
