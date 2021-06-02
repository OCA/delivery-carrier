#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Delivery Carrier Roulier",
    "version": "14.0.1.0.0",
    "author": "Akretion,Odoo Community Association (OCA)",
    "summary": "Integration of multiple carriers",
    "maintainers": ["florian-dacosta"],
    "category": "Warehouse",
    "depends": [
        "partner_helper",
        "base_phone",  # from oca/telephony
        "base_delivery_carrier_label",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "views/stock_quant_package.xml",
        "views/carrier_account.xml",
    ],
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
