# Copyright 2023 Ángel García de la Chica Herrera <angel.garcia@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    extra_information_package_label = fields.Boolean(
        string="Print extra information package label",
        config_parameter="delivery_package_number.extra_information_package_label",
    )
    report_package_label_page_height = fields.Integer(
        string="Page height",
        default=100,
        config_parameter="delivery_package_number.report_package_label_page_height",
    )

    @api.onchange("report_package_label_page_height", "extra_information_package_label")
    def _onchange_report_package_label_page_height(self):
        paperformat = self.env.ref(
            "delivery_package_number.paperformat_number_of_packages_label"
        )
        if paperformat:
            paperformat.page_height = (
                self.report_package_label_page_height
                if self.extra_information_package_label is True
                else 50
            )
