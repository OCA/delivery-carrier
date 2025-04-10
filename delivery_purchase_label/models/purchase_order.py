# Copyright 2024 Camptocamp SA
# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError


class SameDeliveryLabelGenerated(Exception):
    pass


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    vendor_label_carrier_id = fields.Many2one(
        "delivery.carrier",
        "Vendor Label Carrier",
        domain=[("purchase_label_picking_type", "!=", False)],
    )
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
        self._generate_purchase_delivery_label()
        return super().action_rfq_send()

    def button_cancel(self):
        self._cancel_purchase_delivery_label_picking()
        return super().button_cancel()

    def _is_valid_for_vendor_labels(self):
        self.ensure_one()
        if self.state not in self._states_to_generate_delivery_label():
            return False
        if not self.dest_address_id:
            return False
        if not any(
            product.type in ["product", "consu"]
            for product in self.order_line.product_id
        ):
            return False
        if not self.vendor_label_carrier_id.purchase_label_picking_type:
            return False
        return True

    def _are_delivery_label_equivalent(self, pick_1, pick_2):
        if len(pick_1.move_lines) != len(pick_2.move_lines):
            return False
        for move_old, move_new in zip(pick_1.move_lines, pick_2.move_lines):
            if (
                move_old.product_id != move_new.product_id
                or move_old.product_uom_qty != move_new.product_uom_qty
            ):
                return False
        return True

    def _generate_purchase_delivery_label(self):
        """Create a transfer to generate the carrier labels."""
        self.ensure_one()
        if not self._is_valid_for_vendor_labels():
            return
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(
                _(
                    "You must set a Vendor Location for this partner %s",
                    self.partner_id.name,
                )
            )
        carrier = self.vendor_label_carrier_id
        order = self.with_company(self.company_id)
        new_label_picking = None
        try:
            with self.env.cr.savepoint():
                # Using a savepoint for generating the transfer for the label
                # and keep the new one only if it is different
                new_label_picking = order._create_purchase_delivery_label_picking(
                    carrier
                )
                if self._are_delivery_label_equivalent(
                    new_label_picking, order.delivery_label_picking_id
                ):
                    new_label_picking = None
                    raise SameDeliveryLabelGenerated
        except SameDeliveryLabelGenerated:
            pass
        if not new_label_picking:
            return
        if order.delivery_label_picking_id:
            order._cancel_purchase_delivery_label_picking()
        order.delivery_label_picking_id = new_label_picking
        new_label_picking.message_post_with_view(
            "mail.message_origin_link",
            values={"self": new_label_picking, "origin": self},
            subtype_id=self.env.ref("mail.mt_note").id,
        )

    def _create_stock_moves_for_delivery_label_picking(self, picking):
        res = self.env["stock.move"]
        for line in self.order_line:
            moves = line._create_stock_moves(picking)
            moves.delivery_label_purchase_line_id = line
            res |= moves

        return res

    def _create_purchase_delivery_label_picking(self, carrier):
        self.ensure_one()
        values = self._get_purchase_delivery_label_picking_value(carrier)
        picking = self.env["stock.picking"].with_user(SUPERUSER_ID).create(values)
        moves = self._create_stock_moves_for_delivery_label_picking(picking)
        moves.location_id = picking.location_id
        moves.location_dest_id = picking.location_dest_id
        # Remove the link on the sale and purchase
        # To not impact the delivered quantity on them
        picking.sale_id = False
        moves.sale_line_id = False
        moves.purchase_line_id = False
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking._action_done()
        return picking

    def _cancel_purchase_delivery_label_picking(self):
        delivery_label_pickings = self.delivery_label_picking_id
        for picking in delivery_label_pickings:
            picking.cancel_shipment()
        # Using wirte to by pass internal checks, not a problem
        # because this is a fake move (Vendor to Vendor)
        delivery_label_pickings.move_line_ids.write({"state": "cancel"})
        delivery_label_pickings.move_lines.write({"state": "cancel"})
        delivery_label_pickings.write({"state": "cancel"})

    def _get_purchase_delivery_label_picking_value(self, carrier):
        return {
            "picking_type_id": carrier.purchase_label_picking_type.id,
            "partner_id": self.dest_address_id.id,
            "user_id": False,
            "date": fields.Datetime.now(),
            "origin": " - ".join(
                [origin for origin in [self.origin, self.name] if origin]
            ),
            "location_dest_id": self.partner_id.property_stock_supplier.id,
            "location_id": self.partner_id.property_stock_supplier.id,
            "company_id": self.company_id.id,
            "carrier_id": carrier.id,
            "delivery_label_purchase_id": self.id,
        }
