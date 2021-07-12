# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Delivery Roulier Option",
    "version": "14.0.1.0.0",
    "author": "Akretion,Odoo Community Association (OCA)",
    "summary": "Add options to roulier modules",
    "maintainers": ["florian-dacosta"],
    "category": "Warehouse",
    "depends": [
        "delivery_roulier",
        "product_harmonized_system",  # from OCA/intrastat-extrastat
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "data/delivery.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
