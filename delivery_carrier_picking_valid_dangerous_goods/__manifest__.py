# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Delivery Carrier Valid - Dangerous Goods",
    "summary": "Checks if a transfer matches carrier dangerous goods restrictions",
    "version": "18.0.1.0.0",
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["mmequignon"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "delivery_carrier_picking_valid",
        "l10n_eu_product_adr_dangerous_goods",
    ],
    "data": ["views/delivery_carrier.xml"],
}
