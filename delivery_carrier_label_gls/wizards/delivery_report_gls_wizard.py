# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DeliveryReportGls(models.TransientModel):
    _name = "delivery.report.gls.wizard"
    _description = "Wizard to get the End of Day Report"

    @api.model
    def _default_carriers(self):
        return self.env["delivery.carrier"].search([("delivery_type", "=", "gls")])

    carrier_ids = fields.Many2many(
        comodel_name="delivery.carrier",
        string="Carriers",
        default=_default_carriers,
        domain=[("delivery_type", "=", "gls")],
    )
    date = fields.Date(default=False)

    @api.constrains
    def _constrain_carrier_id(self):
        for record in self:
            if any(carrier.delivery_type != "gls" for carrier in record.carrier_ids):
                raise ValidationError(_("Only GLS supports delivery reports."))

    @api.model
    def cron(self):
        return self.create({})._get_end_of_day_report()

    def get_end_of_day_report(self):
        self.ensure_one()
        reports = self._get_end_of_day_report()
        if not reports:
            raise ValidationError(_("There are no new shipments."))
        action_xmlid = "delivery_carrier_label_gls.delivery_report_gls_act_window"
        window_action = self.env.ref(action_xmlid).read()[0]
        window_action["target"] = "current"
        window_action["view_mode"] = "form" if len(reports) == 1 else "tree"
        if len(reports) == 1:
            window_action["res_id"] = reports.id
            window_action["views"] = [(False, "form")]
        else:
            window_action["views"] = [(False, "tree"), (False, "form")]
            window_action["domain"] = [("id", "in", reports.ids)]
        return window_action

    def _get_end_of_day_report(self):
        reports = self.env["delivery.report.gls"].browse()
        for carrier in self.carrier_ids:
            # TODO: actually process each login only once.
            reports |= self._get_carrier_end_of_day_report(carrier)
        return reports

    def _get_carrier_end_of_day_report(self, delivery_carrier):
        # there could be multiple reports in one call,
        # since carrier is login/Contact ID,
        # but this returns all contact IDs for the login...
        # TODO: rollback or any other error: leave a trace other than the logs
        reports = self.env["delivery.report.gls"].browse()
        now = fields.Datetime.now()  # TODO: if date is today, use now instead
        date = self.date or now
        report_api = delivery_carrier._get_gls_client().get_end_of_day_report(date=date)
        packages_api = report_api.get("Shipments", [])
        if packages_api:
            track_ids = []
            for shipment in packages_api:
                for unit in shipment["ShipmentUnit"]:
                    track_ids.append(unit["TrackID"])
            domain_packages = [("parcel_tracking", "in", track_ids)]
            packages = self.env["stock.quant.package"].search(domain_packages)
            if len(packages) != len(packages_api):
                _logger.exception("End of day report: wrong number of packages!")
            for carrier in packages.mapped("carrier_id"):
                vals_report = {"report_datetime": date or now, "carrier_id": carrier.id}
                report = self.env["delivery.report.gls"].create(vals_report)
                report_pkgs = packages.filtered(lambda p, c=carrier: p.carrier_id == c)
                report_pkgs.write({"report_id": report.id})
                reports |= report
        return reports
