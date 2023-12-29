#####################################################################################
# Copyright (c) 2023 Grüne Erde GmbH (https://grueneerde.com)
# All Right Reserved
#
# Licensed under the Odoo Proprietary License v1.0 (OPL).
# See LICENSE file for full licensing details.
#####################################################################################
{
    "name": "RMA Analytics",
    "summary": """This module extends the standard functionality for analytics.
    In the GE context this mainly includes
    reports for complaint reasons and time at customer.""",
    "version": "15.0.1.0.0",
    "category": "Inventory",
    "author": "Grüne Erde",  # pylint: disable=all
    "website": "https://github.com/grueneerde/ge_complaint_types",
    "license": "OPL-1",
    "depends": [
        "base",
        "delivery",
        "stock",  # for adding to settings menu
        "delivery_state",  # used for tracking and basic interface in stock -> Additional Information
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/dhl.ice.csv",
        "data/dhl.ric.csv",
        "data/dhl.event.csv",
        "views/res_company_views.xml",
        "views/stock_picking_views.xml",
        "views/tracking_event_views.xml",
        "views/stock_quant_package_views.xml",
    ],
    "external_dependencies": {"python": ["dicttoxml", "xmltodict"]},
}
