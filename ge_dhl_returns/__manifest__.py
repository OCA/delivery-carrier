#####################################################################################
# Copyright (c) 2023 Grüne Erde GmbH (https://grueneerde.com)
# All Right Reserved
#
# Licensed under the Odoo Proprietary License v1.0 (OPL).
# See LICENSE file for full licensing details.
#####################################################################################
{
    "name": "DHL Parcel DE Returns (Post & Parcel Germany)",
    "summary": """This module implements the DHL API for creating return labels.""",
    "version": "15.0.1.0.0",
    "category": "Inventory",
    "author": "Grüne Erde",  # pylint: disable=all
    "website": "https://github.com/grueneerde/ge_complaint_types",
    "license": "OPL-1",
    "depends": [
        "base",
        "delivery",
        "ge_dhl_base",  # for an simplified interface and RequestBase
        "base_address_extended",  # needed for street_number
    ],
    "data": ["views/stock_picking_views.xml", "views/res_company_views.xml"],
    "demo": [],
}
