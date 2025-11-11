# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Delivery CBL",
    "summary": "Integrate CBL webservice",
    "version": "17.0.1.1.1",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["delivery_package_number", "base_delivery_carrier_label"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "report/cbl_manifest.xml",
        "views/delivery_carrier_view.xml",
        "views/stock_picking_views.xml",
        "wizard/wizard_confirm_cbl_pickings_view.xml",
    ],
}
