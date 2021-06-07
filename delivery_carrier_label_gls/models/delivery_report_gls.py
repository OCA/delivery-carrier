# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DeliveryReport(models.Model):
    _name = "delivery.report.gls"

    report_datetime = fields.Datetime(
        string="Report Date and Time", required=True, readonly=True
    )
    carrier_id = fields.Many2one(
        "delivery.carrier", string="Carrier", required=True, readonly=True
    )
    package_ids = fields.One2many(
        "stock.quant.package", "report_id", "Pickings", readonly=True,
    )

    @api.depends("carrier_id", "report_datetime")
    def _compute_display_name(self):
        for record in self:
            carrier_name = record.carrier_id.name or "GLS"
            record.display_name = "{}/{}".format(carrier_name, record.report_datetime)
