{
    "name": "Delivery DPD Portugal",
    "summary": "Integrate DPD Portugal shipping operations from Odoo",
    "version": "19.0.1.1.0",
    "category": "Inventory/Delivery",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/OCA/delivery-carrier",
    "license": "AGPL-3",
    "depends": [
        "delivery_carrier_account",
        "delivery_carrier_agency",
        "delivery_package_number",
        "stock_delivery",
    ],
    "data": [
        "views/delivery_carrier.xml",
        "views/stock_picking.xml",
    ],
    "installable": True,
    "application": False,
}
