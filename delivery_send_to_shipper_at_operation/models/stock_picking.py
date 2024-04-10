# Copyright 2021 Camptocamp SA
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from lxml import etree

from odoo import fields, models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

from odoo.addons.base.models.ir_ui_view import (
    transfer_modifiers_to_node,
    transfer_node_to_modifiers,
)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_notification_sent = fields.Boolean(default=False, copy=False)

    def _send_confirmation_email(self):
        picking_ids_skip_costs = []
        for picking in self:
            if not picking._is_send_to_shipper_at_operation():
                continue
            picking_ids_skip_costs.append(picking.id)
            picking.carrier_id = picking.ship_picking_id.carrier_id
        pickings_skip_costs = self.browse(picking_ids_skip_costs)
        if pickings_skip_costs:
            pickings_skip_costs._handle_send_to_shipper_at_operation()
        super(StockPicking, self - pickings_skip_costs)._send_confirmation_email()

    def _handle_send_to_shipper_at_operation(self):
        """Send the delivery notice to the carrier from a specific operation type.

        We are only interested by sending the delivery notice, the delivery fee
        still have to be added to the SO by the ship operation.
        """
        super().with_context(skip_delivery_cost=True)._send_confirmation_email()
        for picking in self:
            related_ship = picking.ship_picking_id
            values = picking._prepare_values_send_to_ship_at_operation(related_ship)
            related_ship.write(values)

    def _is_send_to_shipper_at_operation(self):
        """Return True if the operation needs to send the delivery notice."""
        self.ensure_one()
        if not self.carrier_id:
            # If the current operation has no carrier defined, but a carrier
            # has been found from the ship and is configured to match the
            # current operation type: force the sending of the delivery notice
            # to the carrier
            related_ship = self.ship_picking_id
            carrier = related_ship.carrier_id
            if (
                carrier.integration_level == "rate_and_ship"
                and carrier.send_delivery_notice_on == "custom"
                and self.picking_type_id
                in carrier.send_delivery_notice_picking_type_ids
            ):
                return True
        return False

    def _prepare_values_send_to_ship_at_operation(self, related_ship):
        self.ensure_one()
        related_ship.ensure_one()
        carrier_tracking_ref = related_ship.carrier_tracking_ref
        if carrier_tracking_ref:
            carrier_tracking_ref += "," + self.carrier_tracking_ref
        else:
            carrier_tracking_ref = self.carrier_tracking_ref
        return {
            "delivery_notification_sent": True,
            "carrier_price": self.carrier_price,
            "carrier_tracking_ref": carrier_tracking_ref,
        }

    def send_to_shipper(self):
        # Do not send delivery notice to the carrier if it has already been sent
        # through a previous operation (like a pack)
        self.ensure_one()
        if self.delivery_notification_sent:
            # But we still need to add the delivery cost to the SO
            self._add_delivery_cost_to_so()
            return False
        return super().send_to_shipper()

    def _add_delivery_cost_to_so(self):
        if self.env.context.get("skip_delivery_cost"):
            return
        return super()._add_delivery_cost_to_so()

    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        # Override to hide the "Send to shipper" button if the delivery
        # notification has already been sent
        result = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if result.get("name") == "stock.picking.form":
            result["arch"] = self._fields_view_get_adapt_send_to_shipper_attrs(
                result["arch"]
            )
        return result

    def _fields_view_get_adapt_send_to_shipper_attrs(self, view_arch):
        """Hide 'Send to Shipper' button if 'delivery_notification_sent' is True."""
        doc = etree.XML(view_arch)
        xpath_expr = "//button[@name='send_to_shipper']"
        attrs_key = "invisible"
        nodes = doc.xpath(xpath_expr)
        for field in nodes:
            attrs = safe_eval(field.attrib.get("attrs", "{}"))
            if not attrs[attrs_key]:
                continue
            invisible_domain = expression.OR(
                [attrs[attrs_key], [("delivery_notification_sent", "=", True)]]
            )
            attrs[attrs_key] = invisible_domain
            field.set("attrs", str(attrs))
            modifiers = {}
            transfer_node_to_modifiers(
                field, modifiers, self.env.context, current_node_path=["tree"]
            )
            transfer_modifiers_to_node(modifiers, field)
        return etree.tostring(doc, encoding="unicode")

    def _create_backorder(self):
        backorders = super()._create_backorder()
        for backorder in backorders:
            delivery_notification_sent = (
                backorder.backorder_id.delivery_notification_sent
            )
            if delivery_notification_sent:
                backorder.delivery_notification_sent = delivery_notification_sent
        return backorders
