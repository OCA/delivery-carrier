# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    date_shipped = fields.Date(
        string='Shipment Date',
        readonly=True,
    )
    date_delivered = fields.Datetime(
        string='Delivery Date',
        readonly=True,
    )
    tracking_state = fields.Char(
        string='Tracking state',
        readonly=True,
        index=True,
        track_visibility='always',
    )
    tracking_state_history = fields.Text(
        string='Tracking state history',
        readonly=True,
    )
    delivery_state = fields.Selection(
        selection=[
            ('shipping_recorded_in_carrier', 'Shipping recorded in carrier'),
            ('in_transit', 'In transit'),
            ('canceled_shipment', 'Canceled shipment'),
            ('incidence', 'Incidence'),
            ('customer_delivered', 'Customer delivered'),
            ('warehouse_delivered', 'Warehouse delivered'),
        ],
        string='Carrier State',
        track_visibility='onchange',
        readonly=True,
    )

    def tracking_state_update(self):
        """Call to the service provider API which should have the method
        defined in the model as:
            <my_provider>_tracking_state_update
        It can be triggered manually or by the cron."""
        for picking in self.filtered("carrier_id"):
            method = '%s_tracking_state_update' % picking.delivery_type
            if hasattr(picking.carrier_id, method):
                getattr(picking.carrier_id, method)(picking)

    @api.model
    def _update_delivery_state(self):
        """Automated action to query the delivery states to the carriers API.
        every carrier should implement it 's own method. We split them by
        delivery type so only those carries with the method update"""
        pickings = self.search([
            ("state", "=", "done"),
            ("delivery_state", "not in",
                ["customer_delivered", "canceled_shipment"]),
            # These won't ever autoupdate, so we don't want to evaluate them
            ("delivery_type", "not in", [False, "fixed", "base_one_rule"]),
        ])
        pickings.tracking_state_update()

    def _get_delivery_mail_context(self):
        """Extensible context for customization"""
        delivery_template_id = self.env.ref(
            "delivery_state.delivery_notification").id
        return dict(
            default_composition_mode="comment",
            default_email_from=self.company_id.email,
            default_res_id=self.id,
            default_model="stock.picking",
            default_use_template=bool(delivery_template_id),
            default_template_id=delivery_template_id,
            custom_layout="mail.mail_notification_light"
        )

    def force_shipping_confirmation_email_send(self):
        """We'll be using the core method but with a different template as
        we want to ensure that the shipping notification is sent to the right
        person. For example, a customer pays for a present that will be sent to
        a friend. The confirmation email should go to him. Sending it to the
        friend, would spoil the surprise"""
        for picking in self:
            email_act = picking.action_send_confirmation_email()
            if email_act:
                email_ctx = picking._get_delivery_mail_context()
                picking.with_context(**email_ctx).message_post_with_template(
                    email_ctx.get("default_template_id"))
        return True

    def send_to_shipper(self):
        """Send delivery email to customer if configured"""
        super().send_to_shipper()
        partner = self.sale_id.partner_id or self.partner_id
        send_delivery = all({
            self.company_id.send_delivery_confirmation,
            partner,
            self.carrier_id,
        })
        if not send_delivery:
            return
        self.force_shipping_confirmation_email_send()
