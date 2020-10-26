# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Delivery Carrier GLS (fr)",
    "version": "12.0.0.1.0",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintener": "Akretion",
    "category": "Warehouse",
    "summary": "GLS carrier label printing",
    "depends": [
        "base_delivery_carrier_label",
        "partner_helper",
        "delivery_roulier",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "data/delivery_carrier.xml",
        "data/sequence.xml",
        "views/account_carrier_view.xml",
    ],
    "demo": [
        "demo/company.xml",
        "demo/stock_picking.xml",
        "demo/stock.move.csv",
    ],
    "external_dependencies": {
        "python": [
            "roulier",
        ],
    },
    "license": "AGPL-3",
    "installable": True,
}
