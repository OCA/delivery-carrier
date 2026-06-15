# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2026 Raumschmiede GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

from markupsafe import Markup

from odoo import _, api, fields, models

DELIVERY_STATE_SHIPPING_RECORDED = "shipping_recorded_in_carrier"
DELIVERY_STATE_IN_TRANSIT = "in_transit"
DELIVERY_STATE_CANCELED = "canceled_shipment"
DELIVERY_STATE_INCIDENCE = "incidence"
DELIVERY_STATE_CUS_DELIVERED = "customer_delivered"
DELIVERY_STATE_WH_DELIVERED = "warehouse_delivered"
DELIVERY_STATE_NO_UPDATE = "no_update"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    date_shipped = fields.Date(
        string="Shipment Date",
        readonly=True,
        copy=False,
    )
    date_delivered = fields.Datetime(
        string="Delivery Date",
        readonly=True,
        copy=False,
    )
    # Technical field to store raw tracking data from the carrier API
    tracking_json = fields.Char(readonly=True, copy=False)
    tracking_state = fields.Char(
        string="Tracking state",
        readonly=True,
        index=True,
        tracking=True,
        copy=False,
    )
    tracking_state_history = fields.Text(
        string="Tracking state history",
        readonly=True,
        copy=False,
    )
    delivery_state = fields.Selection(
        selection=[
            (DELIVERY_STATE_SHIPPING_RECORDED, "Shipping recorded in carrier"),
            (DELIVERY_STATE_IN_TRANSIT, "In transit"),
            (DELIVERY_STATE_CANCELED, "Canceled shipment"),
            (DELIVERY_STATE_INCIDENCE, "Incidence"),
            (DELIVERY_STATE_CUS_DELIVERED, "Customer delivered"),
            (DELIVERY_STATE_WH_DELIVERED, "Warehouse delivered"),
            (DELIVERY_STATE_NO_UPDATE, "No more updates from carrier"),
        ],
        string="Carrier State",
        tracking=True,
        readonly=True,
        copy=False,
    )
    pod_file = fields.Binary(
        string="Proof of Delivery File",
        readonly=True,
        copy=False,
    )
    pod_filename = fields.Char(
        string="Proof of Delivery Filename",
        readonly=True,
        copy=False,
    )
    pod_error = fields.Char(
        string="Proof of Delivery Error",
        readonly=True,
        copy=False,
    )

    def _get_delivery_states_in_progress(self):
        return [
            DELIVERY_STATE_SHIPPING_RECORDED,
            DELIVERY_STATE_IN_TRANSIT,
            DELIVERY_STATE_INCIDENCE,
            DELIVERY_STATE_WH_DELIVERED,
        ]

    def tracking_state_update(self):
        """Call to the service provider API which should have the method
        defined in the model as:
            <my_provider>_tracking_state_update
        It can be triggered manually or by the cron."""
        for picking in self:
            method = "%s_tracking_state_update" % picking.delivery_type
            carrier = picking.carrier_id

            if not carrier or not hasattr(carrier, method):
                picking.delivery_state = DELIVERY_STATE_NO_UPDATE
                continue

            try:
                with self.env.cr.savepoint():
                    getattr(carrier, method)(picking)
            except Exception as e:
                if not self.env.context.get("lastcall"):
                    raise
                picking.pod_error = str(e)

            days = carrier.days_fetch_tracking_state_update
            if (
                picking.delivery_state
                in [
                    DELIVERY_STATE_CUS_DELIVERED,
                    DELIVERY_STATE_CANCELED,
                    DELIVERY_STATE_NO_UPDATE,
                ]
                or days <= 0
            ):
                continue

            date_tracking_started = None
            if picking.date_shipped:
                date_tracking_started = fields.Datetime.to_datetime(
                    picking.date_shipped
                )
            else:
                date_tracking_started = picking.date_done

            if date_tracking_started <= datetime.now() - timedelta(days=days):
                picking.delivery_state = DELIVERY_STATE_NO_UPDATE

        # Filter pickings with errors and notify
        pickings_with_errors = self.filtered("pod_error")
        if pickings_with_errors:
            pickings_with_errors._send_message_pod_error()

    @api.model
    def _update_delivery_state(self):
        """Automated action to query the delivery states to the carriers API.
        every carrier should implement it 's own method. We split them by
        delivery type so only those carries with the method update"""
        pickings = self.search(
            [
                ("state", "=", "done"),
                (
                    "delivery_state",
                    "in",
                    self._get_delivery_states_in_progress(),
                ),
                # These won't ever autoupdate, so we don't want to evaluate them
                ("delivery_type", "not in", [False, "fixed", "base_on_rule"]),
            ]
        )
        pickings.tracking_state_update()

    def _send_message_pod_error(self):
        for picking in self:
            message = picking._build_message_pod_error()
            picking.message_post(body=Markup(message))

    def _build_message_pod_error(self):
        self.ensure_one()

        return _(
            "<b>Errors while fetching POD for carrier %s:</b><br/>"
            "Please review the details below "
            "and take the necessary actions to resolve these issues.: %s<br/>",
            self.carrier_id.name,
            self.pod_error,
        )
