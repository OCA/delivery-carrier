# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    delivery_label_picking_id = fields.Many2one(
        "stock.picking",
        "Delivery Label Picking",
        store=True,
        readonly=True,
    )

    @api.model
    def _states_to_generate_delivery_label(self):
        """Labels will be (re)generated only if the PO is in one of these states."""
        return ["draft", "sent"]

    @api.model
    def _mail_templates_to_not_attach_labels(self):
        return self.env.ref("purchase.email_template_edi_purchase_reminder").ids

    def action_rfq_send(self):
        self.ensure_one()
        if self._states:
            self._generate_purchase_delivery_label()
        return super().action_rfq_send()

    def button_send_label(self):
        self._generate_purchase_delivery_label()

    def _is_valid_for_vendor_labels(self):
        self.ensure_one()
        if not self.dest_address_id:
            return False
        return True

    def _generate_purchase_delivery_label(self):
        """Create a transfer to generate the carrier labels."""
        self.ensure_one()
        if self.state not in self._states_to_generate_delivery_label():
            return
        if not self._is_valid_for_vendor_labels():
            return
        if not any(
            product.type in ["product", "consu"]
            for product in self.order_line.product_id
        ):
            return
        # Find the carrier and that will be used
        carrier = self.partner_id.purchase_delivery_carrier_id
        if not carrier.purchase_label_picking_type:
            return
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(
                _(
                    "You must set a Vendor Location for this partner %s",
                    self.partner_id.name,
                )
            )
        order = self.with_company(self.company_id)
        # Create and process the transer to send the labels
        values = order._get_purchase_delivery_label_picking_value(carrier)
        picking = self.env["stock.picking"].with_user(SUPERUSER_ID).create(values)
        moves = order.order_line._create_stock_moves(picking)
        moves.purchase_line_id = False
        picking.action_assign()
        for move in moves:
            move.quantity_done = move.product_uom_qty
        picking._action_done()
        order.delivery_label_picking_id = picking
        picking.message_post_with_view(
            "mail.message_origin_link",
            values={"self": picking, "origin": self},
            subtype_id=self.env.ref("mail.mt_note").id,
        )

    def _get_purchase_delivery_label_picking_value(self, carrier):
        return {
            "picking_type_id": carrier.purchase_label_picking_type.id,
            "partner_id": self.dest_address_id.id,
            "user_id": False,
            "date": fields.Datetime.now(),
            "origin": self.name,
            "location_dest_id": self.partner_id.property_stock_supplier.id,
            "location_id": self.partner_id.property_stock_supplier.id,
            "company_id": self.company_id.id,
            "carrier_id": carrier.id,
        }
