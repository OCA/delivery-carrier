# Copyright 2016 Raphael REVERDY <raphael.reverdy@akretion.com>
#        EBII MonsieurB <monsieurb@saaslys.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Delivery Carrier DPD (fr)",
    "version": "14.0.1.0.0",
    "author": "Akretion, Odoo Community Association (OCA)",
    "summary": "Generate Labels for DPD",
    "category": "Warehouse",
    "depends": [
        "delivery_roulier",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": ["data/delivery.xml", "data/keychain.xml"],
    "external_dependencies": {
        "python": [
            "cerberus",
        ],
    },
    "installable": True,
    "license": "AGPL-3",
}
