#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Delivery Carrier Roulier",
    "version": "16.0.1.0.0",
    "author": "Akretion,Odoo Community Association (OCA)",
    "summary": "Integration of multiple carriers",
    "maintainers": ["florian-dacosta"],
    "category": "Delivery",
    "depends": [
        "base_delivery_carrier_label",
        "delivery_carrier_account",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [],
    "demo": [
        "demo/product.xml",
    ],
    "external_dependencies": {
        "python": [
            "roulier",  # '>0.2.0'
        ],
    },
    "installable": True,
    "license": "AGPL-3",
}
