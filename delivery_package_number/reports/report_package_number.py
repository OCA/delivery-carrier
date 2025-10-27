# Copyright 2020 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ReportDeliveryPackageNumber(models.AbstractModel):
    _name = "report.delivery_package_number.delivery_package_number_report"
    _description = "Delivery Package Number Report"

    def _get_report_values(self, docids, data=None):
        picking_ids = self.env["stock.picking"].browse(docids)
        extra_information = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("delivery_package_number.extra_information_package_label")
        )
        return {"docs": picking_ids, "extra_information": extra_information}
