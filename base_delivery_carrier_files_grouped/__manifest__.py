# Copyright 2020 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Base Delivery Carrier Files Grouped",
    "summary": "Groups Delivery Carrier lines of delivery carriers by partner",
    "version": "12.0.1.0.0",
    "category": "Generic Modules/Warehouse",
    "website": "https://www.planetatic.com/",
    "author": "PlanetaTIC",
    "maintainers": ["PlanetaTIC"],
    "license": "LGPL-3",
    "depends": [
        "base_delivery_carrier_files",
    ],
    "data": [
        'views/partner_view.xml',
    ],
    "application": False,
    "installable": True,
}
