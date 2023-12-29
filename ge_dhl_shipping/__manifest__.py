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
        "base_iso3166",
        "ge_dhl_base",
        # dhl doesn't support rate infos therefore
        # it's necessary to manually set the price / price rules
        "delivery_price_method",
    ],
    "data": ["view/res_company.xml", "view/delivery_carrier.xml"],
}
