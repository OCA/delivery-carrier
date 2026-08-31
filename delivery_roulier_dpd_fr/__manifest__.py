# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Delivery Carrier DPD FR",
    "version": "14.0.1.0.0",
    "author": "Akretion, Odoo Community Association (OCA)",
    "summary": "Generate Labels for DPD",
    "category": "Warehouse",
    "depends": [
        "delivery_roulier",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "views/carrier_account_views.xml",
        "data/product.product.xml",
        "data/delivery_carrier.xml",
    ],
    "demo": [
        "demo/carrier_account.xml",
    ],
    "external_dependencies": {
        "python": [
            "cerberus",
        ],
    },
    "installable": True,
    "license": "AGPL-3",
}
