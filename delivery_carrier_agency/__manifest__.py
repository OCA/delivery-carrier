# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "Delivery Carrier Agency",
    "summary": "Add a model for Carrier Agencies",
    "version": "17.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Akretion,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock_delivery",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/delivery_carrier_agency_view.xml",
    ],
    "demo": [],
    "qweb": [],
}
