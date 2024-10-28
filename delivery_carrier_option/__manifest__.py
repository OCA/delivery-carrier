# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Delivery Carrier Option",
    "version": "18.0.1.0.0",
    "author": "Camptocamp,Akretion,Odoo Community Association (OCA)",
    "category": "Delivery",
    "maintainers": ["florian-dacosta"],
    "depends": [
        "stock_delivery",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "views/stock_picking.xml",
        "views/delivery_carrier.xml",
        "security/ir.model.access.csv",
        "views/delivery_carrier_template_option.xml",
        "views/delivery_carrier_option.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
