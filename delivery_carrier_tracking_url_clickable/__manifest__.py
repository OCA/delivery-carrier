# Copyright - 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Tracking URL Clickable Extension",
    "summary": "Converts tracking references to clickable links in stock pickings",
    "version": "16.0.1.0.0",
    "category": "Warehouse",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Therp BV, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["delivery_carrier_default_tracking_url"],
    "data": [
        "views/stock_picking_views.xml",
        "views/delivery_carrier_views.xml",
    ],
    "installable": True,
    "application": False,
    "maintainers": ["ntsirintanis"],
}
