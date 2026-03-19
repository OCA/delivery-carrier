# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo import SUPERUSER_ID, api, fields, models
from odoo.fields import Domain


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
    tracking_json = fields.Json(readonly=True, copy=False)
    tracking_state = fields.Char(
        readonly=True,
        index=True,
        tracking=True,
        copy=False,
    )
    tracking_state_history = fields.Text(
        readonly=True,
        copy=False,
    )
    delivery_state = fields.Selection(
        selection=[
            ("shipping_recorded_in_carrier", "Shipping recorded in carrier"),
            ("in_transit", "In transit"),
            ("canceled_shipment", "Canceled shipment"),
            ("incident", "Incident"),
            ("customer_delivered", "Customer delivered"),
            ("warehouse_delivered", "Warehouse delivered"),
            ("no_update", "No more updates from carrier"),
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

    def tracking_state_update(self):
        """Call to the service provider API which should have the method
        defined in the model as:
            <my_provider>_tracking_state_update
        It can be triggered manually or by the cron."""
        for picking in self.filtered("carrier_id"):
            method = f"{picking.delivery_type}_tracking_state_update"
            if hasattr(picking.carrier_id, method):
                try:
                    with self.env.cr.savepoint():
                        getattr(picking.carrier_id, method)(picking)
                except Exception as e:
                    if not self.env.context.get("cron_id"):
                        raise
                    picking.pod_error = str(e)
        # Filter pickings with errors and notify
        pickings_with_errors = self.filtered("pod_error")
        if pickings_with_errors:
            pickings_with_errors._send_message_pod_error()

    @api.model
    def _update_delivery_state(self):
        """Automated action to query the delivery states to the carriers API.
        every carrier should implement it 's own method. We split them by
        delivery type so only those carries with the method update"""
        domain = Domain(
            [
                ("state", "=", "done"),
                (
                    "delivery_state",
                    "not in",
                    ["customer_delivered", "canceled_shipment", "no_update"],
                ),
                # These won't ever autoupdate, so we don't want to evaluate them
                ("delivery_type", "not in", [False, "fixed", "base_one_rule"]),
            ]
        )
        pickings = self.search(domain)
        pickings.tracking_state_update()

    def _send_message_pod_error(self):
        channel_admin = self.env.ref("mail.channel_admin", raise_if_not_found=False)
        if not channel_admin:
            return
        pickings_by_carrier = self.grouped("carrier_id")
        for _carrier, pickings in pickings_by_carrier.items():
            message = pickings._build_message_pod_error()
            channel_admin.with_user(SUPERUSER_ID).message_post(body=Markup(message))

    def _build_message_pod_error(self):
        message = self.env._(
            "<b>Errors while fetching POD for carrier %s:</b><br/>"
            "Please review the details below "
            "and take the necessary actions to resolve these issues.:<br/>",
            self.carrier_id.name,
        )
        message += "<ul>"
        for picking in self:
            picking_url = picking._get_html_link()
            message += f"<li>Picking {picking_url}: {picking.pod_error}</li>"
        message += "</ul>"
        return message

    def _send_delivery_state_delivered_email(self):
        for item in self.filtered(
            lambda p: p.company_id.delivery_state_delivered_email_validation
            and p.picking_type_id.code == "outgoing"
            and p.delivery_state == "customer_delivered"
        ):
            source_ref = item.company_id.delivery_state_delivered_mail_template_id
            item.with_context(force_send=True).message_post_with_source(
                source_ref, email_layout_xmlid="mail.mail_notification_light"
            )

    def write(self, vals):
        res = super().write(vals)
        if vals.get("delivery_state") == "customer_delivered":
            self._send_delivery_state_delivered_email()
        return res
