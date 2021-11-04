# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import _, fields, models
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("gefco", "Gefco")])
    gefco_agency_code = fields.Char(string="Gefco Agency Code")
    gefco_shipper_id = fields.Char(string="Gefco Shipper Identification")

    def gefco_get_tracking_link(self, picking):
        partial_1 = "typeSearch=anonymousSearch"
        partial_2 = "searchAnonymous;filterKey=refSend;filterValue="
        return "%s?%s#%s%s" % (
            "https://connect.gefco.net/psc-portal/anonymous.html",
            partial_1,
            partial_2,
            picking.carrier_tracking_ref,
        )

    def gefco_send_shipping(self, pickings):
        return [self.gefco_create_shipping(p) for p in pickings]

    def _gefco_action_labels(self, picking):
        report_name = "delivery_gefco.label_delivery_gefco_template"
        iar = self.env["ir.actions.report"]
        res = iar._get_report_from_name(report_name).render_qweb_text(picking.ids)
        self.env["ir.attachment"].create(
            {
                "name": "GEFCO-%s.zpl" % picking.carrier_tracking_ref,
                "type": "binary",
                "datas": base64.b64encode(res[0]),
                "res_model": picking._name,
                "res_id": picking.id,
            }
        )

    def gefco_create_shipping(self, picking):
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            raise UserError(_("Tracking Reference is required"))
        if not picking.gefco_destination_id:
            raise UserError(_("Gefco destination is required"))
        self._gefco_action_labels(picking)
        return {
            "exact_price": 0,
            "tracking_number": picking.carrier_tracking_ref,
        }

    def gefco_rate_shipment(self, order):
        raise NotImplementedError(_("""Gefco does not allow you to get prices."""))

    def gefco_cancel_shipment(self, pickings):
        raise NotImplementedError(
            _("""Gefco does not allow you to cancel a shipment.""")
        )
