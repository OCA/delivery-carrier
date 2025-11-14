#    Author: David BEAL <david.beal@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Delivery Deposit",
    "version": "14.0.2.0.0",
    "category": "Delivery",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainer": "Akretion",
    "summary": "Create deposit slips",
    "depends": [
        "delivery",
    ],
    "website": "https://github.com/OCA/delivery-carrier",
    "data": [
        "views/deposit_slip_view.xml",
        "views/stock_picking_view.xml",
        "wizards/delivery_deposit_wizard_view.xml",
        "data/ir_sequence_data.xml",
        "report/report.xml",
        "report/deposit_slip.xml",
        "security/ir.model.access.csv",
        "security/model_security.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
