#####################################################################################
# Copyright (c) 2023 Grüne Erde GmbH (https://grueneerde.com)
# All Right Reserved
#
# Licensed under the Odoo Proprietary License v1.0 (OPL).
# See LICENSE file for full licensing details.
#####################################################################################
{
    "name": "DHL API Base",
    "summary": """This module has common functionality for the dhl api.""",
    "version": "15.0.1.0.0",
    "category": "Inventory",
    "author": "Grüne Erde",  # pylint: disable=all
    "website": "https://github.com/grueneerde/ge_complaint_types",
    "license": "OPL-1",
    "depends": ["base", "stock"],
    "data": ["views/stock_picking_views.xml", "views/delivery_carrier_views.xml"],
}
