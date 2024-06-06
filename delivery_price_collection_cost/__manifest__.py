# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Price Collection Cost",
    "summary": "Add delivery collection costs as a separate line in the SO",
    "author": "PyTech SRL, Ooops, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/delivery-carrier",
    "license": "AGPL-3",
    "category": "Delivery",
    "version": "14.0.1.0.0",
    "depends": ["delivery"],
    "data": [
        "views/delivery_carrier_views.xml",
        "views/delivery_price_rule.xml",
        "wizards/choose_delivery_carrier_views.xml",
    ],
}
