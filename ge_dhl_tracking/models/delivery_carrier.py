# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from .dhl_request import DhlRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def add_tracking_info_to_db(self, tracking_infos):
        # we delete all information for the new piece_codes:
        pice_codes_in_picking = list(
            {d["piece_code"] for d in tracking_infos if "piece_code" in d}
        )
        self.env["tracking.event"].search(
            [("piece_code", "in", pice_codes_in_picking)]
        ).unlink()
        # afterwards we add the new information from the api
        for tracking_info in tracking_infos:
            self.env["tracking.event"].create(tracking_info)

    def dhl_parcel_de_provider_get_tracking_link(self, picking):
        tracking_ids = picking.get_tracking_ids()
        if len(tracking_ids) == 1:
            lang = "de"
            endpoint = (
                "https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html"
            )
            return f"{endpoint}?piececode={tracking_ids[0]}&lang={lang}"
        elif len(tracking_ids) > 1:
            raise UserError(
                _(
                    "There are more than one tracking id please check them at the package level"
                )
            )
        else:
            raise UserError(_("There is no tracking ID available."))

    def dhl_parcel_de_provider_tracking_state_update(self, picking):
        self.ensure_one()
        if picking.carrier_tracking_ref:
            dhl_request = DhlRequest(self, picking)
            response = dhl_request.tracking_state_update()
            picking.delivery_state = response["delivery_state"]
            picking.date_delivered = response["date_delivered"]
