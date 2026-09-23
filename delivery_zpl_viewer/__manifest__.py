# Copyright (c) 2026 Groupe Voltaire
# @author Emilie SOUTIRAS <emilie.soutiras@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Roulier ZPL Label Viewer",
    "summary": "Preview the ZPL shipping labels attached to a transfer",
    "category": "Warehouse",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "application": False,
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Emilie SOUTIRAS, Groupe Voltaire, Odoo Community Association (OCA)",
    "maintainers": ["emiliesoutiras"],
    "depends": [
        "delivery_roulier",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "wizards/zpl_label_viewer_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
