# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from datetime import datetime, time, timedelta, timezone

from odoo import fields, models
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        return_pickings = self.filtered(
            lambda pick: pick.move_ids.origin_returned_move_id
        )
        # For returns, we deal with fee reimburse
        return_pickings._update_delivery_fee_on_return()
        (self - return_pickings)._add_delivery_fee_to_order()
        return res

    def _full_returned(self):
        full_returned = False
        for move in self.move_ids:
            full_returned = not float_compare(
                move.quantity_done,
                sum(
                    move.returned_move_ids.filtered(lambda x: x.state == "done").mapped(
                        "quantity_done"
                    )
                ),
                precision_rounding=move.product_uom.rounding,
            )
            if not full_returned:
                break
        return full_returned

    def _full_returned_for_delivery_fee(self):
        self.ensure_one()
        return self._full_returned()

    def _update_delivery_fee_on_return(self):
        """All pickings returned: we can refund the fee"""
        for sale in self.move_ids.origin_returned_move_id.picking_id.sale_id:
            for fee_line in sale.order_line.filtered("is_delivery_fee"):
                if not self._should_update_delivery_fee_on_return(sale, fee_line):
                    continue
                carrier = fee_line.delivery_fee_picking_id._get_delivery_fee_carrier()
                # No fee refund for this carrier or already returned
                if not carrier.fee_return_percentage or fee_line.product_uom_qty < 1:
                    continue
                # We change the initial demand so the type of invoicing policy doesn't
                # affect in order to trigger the refund.
                fee_line.product_uom_qty = (
                    fee_line.product_uom_qty
                    - (fee_line.product_uom_qty * carrier.fee_return_percentage) / 100
                )

    def _should_update_delivery_fee_on_return(self, sale, fee_line):
        return sale.all_fee_pickings_returned

    def _add_delivery_fee_to_order(self):
        pickings = self.filtered(
            lambda picking: picking._should_add_delivery_fee_to_order()
        )
        for picking in pickings:
            # In the case we want to apply the fee just once
            if (
                picking.company_id.one_delivery_fee_by_sale_order
                and picking.sale_id.order_line.filtered("is_delivery_fee")
            ):
                pickings -= picking
        pickings = pickings._filter_without_delivery_fee_for_commercial_partner_day()
        for picking in pickings:
            picking.sale_id._create_delivery_fee_line(picking)

    def _should_add_delivery_fee_to_order(self):
        self.ensure_one()
        carrier = self._get_delivery_fee_carrier()
        return not (
            self.picking_type_code != "outgoing"
            or not self.sale_id
            or self.partner_id.delivery_fee_exemption
            or not carrier.fee_product_id
        )

    def _get_delivery_fee_carrier(self):
        self.ensure_one()
        return self.carrier_id

    def _filter_without_delivery_fee_for_commercial_partner_day(self):
        groups = {}
        for picking in self:
            if not picking.company_id.one_delivery_fee_by_commercial_partner_day:
                continue
            key = picking._delivery_fee_commercial_partner_day_key()
            groups.setdefault(key, self.env["stock.picking"])
            groups[key] |= picking
        if not groups:
            return self
        day_starts = [key[2] for key in groups]
        next_day_starts = [key[3] for key in groups]
        # Search pickings first to avoid a costly fee-line query joining outward.
        fee_pickings = self.env["stock.picking"].search(
            [
                ("id", "not in", self.ids),
                ("company_id", "in", [key[0] for key in groups]),
                ("partner_id.commercial_partner_id", "in", [key[1] for key in groups]),
                ("date_done", ">=", min(day_starts)),
                ("date_done", "<", max(next_day_starts)),
            ]
        )
        # Batch the fee-line lookup; `seen_keys` preserves first-picking-wins.
        fee_lines = self.env["sale.order.line"]
        if fee_pickings:
            fee_lines = fee_lines.search(
                [
                    ("is_delivery_fee", "=", True),
                    ("order_id.company_id", "in", [key[0] for key in groups]),
                    ("delivery_fee_picking_id", "in", fee_pickings.ids),
                ]
            )
        existing_keys = {
            line.delivery_fee_picking_id._delivery_fee_commercial_partner_day_key()
            for line in fee_lines
        }
        result = self.env["stock.picking"]
        seen_keys = set(existing_keys)
        for picking in self:
            if not picking.company_id.one_delivery_fee_by_commercial_partner_day:
                result |= picking
                continue
            key = picking._delivery_fee_commercial_partner_day_key()
            if key in seen_keys:
                continue
            seen_keys.add(key)
            result |= picking
        return result

    def _delivery_fee_commercial_partner_day_key(self):
        self.ensure_one()
        day_start, next_day_start = self._delivery_fee_local_day_bounds_utc()
        return (
            self.company_id.id,
            self.partner_id.commercial_partner_id.id,
            day_start,
            next_day_start,
        )

    def _delivery_fee_local_day_bounds_utc(self):
        self.ensure_one()
        date_done = self.date_done or fields.Datetime.now()
        # The company rule follows the current user's local day, not the UTC day.
        local_date_done = fields.Datetime.context_timestamp(self, date_done)
        local_day_start = datetime.combine(local_date_done.date(), time.min).replace(
            tzinfo=local_date_done.tzinfo
        )
        local_next_day_start = local_day_start + timedelta(days=1)
        day_start = fields.Datetime.to_string(
            local_day_start.astimezone(timezone.utc).replace(tzinfo=None)
        )
        next_day_start = fields.Datetime.to_string(
            local_next_day_start.astimezone(timezone.utc).replace(tzinfo=None)
        )
        return day_start, next_day_start

    def _has_delivery_fee_for_commercial_partner_day(self):
        self.ensure_one()
        if not self.company_id.one_delivery_fee_by_commercial_partner_day:
            return False
        day_start, next_day_start = self._delivery_fee_local_day_bounds_utc()
        return bool(
            self.env["sale.order.line"].search_count(
                [
                    ("is_delivery_fee", "=", True),
                    ("order_id.company_id", "=", self.company_id.id),
                    ("delivery_fee_picking_id", "!=", self.id),
                    ("delivery_fee_picking_id.date_done", ">=", day_start),
                    ("delivery_fee_picking_id.date_done", "<", next_day_start),
                    (
                        "delivery_fee_picking_id.partner_id.commercial_partner_id",
                        "=",
                        self.partner_id.commercial_partner_id.id,
                    ),
                ],
                limit=1,
            )
        )
