# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Delivery Carrier Account",
    "version": "16.0.1.0.0",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainer": "Akretion",
    "category": "Delivery",
    "depends": [
        "delivery",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "views/carrier_account.xml",
        "views/delivery_carrier.xml",
        "security/ir.model.access.csv",
        "security/carrier_security.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
}
