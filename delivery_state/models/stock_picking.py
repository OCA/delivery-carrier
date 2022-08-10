# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    date_shipped = fields.Date(
        string="Shipment Date",
        readonly=True,
    )
    date_delivered = fields.Datetime(
        string="Delivery Date",
        readonly=True,
    )
    tracking_state = fields.Char(
        readonly=True,
        index=True,
        tracking=True,
    )
    tracking_state_history = fields.Text(
        readonly=True,
    )
    delivery_state = fields.Selection(
        selection=[
            ("shipping_recorded_in_carrier", "Shipping recorded in carrier"),
            ("in_transit", "In transit"),
            ("canceled_shipment", "Canceled shipment"),
            ("incidence", "Incidence"),
            ("customer_delivered", "Customer delivered"),
            ("warehouse_delivered", "Warehouse delivered"),
        ],
        string="Carrier State",
        tracking=True,
        readonly=True,
    )

    def tracking_state_update(self):
        """Call to the service provider API which should have the method
        defined in the model as:
            <my_provider>_tracking_state_update
        It can be triggered manually or by the cron."""
        for picking in self.filtered("carrier_id"):
            method = "%s_tracking_state_update" % picking.delivery_type
            if hasattr(picking.carrier_id, method):
                getattr(picking.carrier_id, method)(picking)

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
                    "not in",
                    ["customer_delivered", "canceled_shipment"],
                ),
                # These won't ever autoupdate, so we don't want to evaluate them
                ("delivery_type", "not in", [False, "fixed", "base_one_rule"]),
            ]
        )
        delivery_types = self.mapped("delivery_type")
        # Split them by delivery type so we can ignore those without the
        # proper method.
        for delivery_type in delivery_types:
            delivery_type_pickings = pickings.filtered(
                lambda x: x.delivery_type == delivery_type
            )
            delivery_type_pickings.tracking_state_update()

    def _send_delivery_state_delivered_email(self):
        for item in self.filtered(
            lambda p: p.company_id.delivery_state_delivered_email_validation
            and p.picking_type_id.code == "outgoing"
            and p.delivery_state == "customer_delivered"
        ):
            template_id = item.company_id.delivery_state_delivered_mail_template_id.id
            item.with_context(force_send=True).message_post_with_template(
                template_id, email_layout_xmlid="mail.mail_notification_light"
            )

    def write(self, vals):
        res = super().write(vals)
        if vals.get("delivery_state") == "customer_delivered":
            self._send_delivery_state_delivered_email()
        return res
