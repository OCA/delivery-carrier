# Copyright 2026 arielbarreiros96 (https://github.com/arielbarreiros96)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import logging

from dateutil.parser import isoparse
from markupsafe import Markup

from odoo import SUPERUSER_ID, Command, api, fields, models

_logger = logging.getLogger(__name__)


class SendcloudReturn(models.Model):
    _inherit = "sendcloud.return"

    picking_id = fields.Many2one(
        "stock.picking", string="Return Operation", readonly=True, copy=False
    )
    original_picking_id = fields.Many2one(
        "stock.picking", string="Original Delivery", readonly=True, copy=False
    )
    odoo_return_error = fields.Char(readonly=True, copy=False)

    def write(self, vals):
        res = super().write(vals)
        if {"label_cost", "picking_id"} & set(vals):
            self._sendcloud_sync_return_cost()
        return res

    def _sendcloud_sync_return_cost(self):
        """Copy the return label cost onto the return operation."""
        for record in self:
            picking = record.picking_id
            if not picking or not record.label_cost:
                continue
            if picking.carrier_price == record.label_cost:
                continue
            picking.with_context(
                skip_sync_picking_to_sendcloud=True
            ).carrier_price = record.label_cost

    @api.model
    def _sendcloud_upsert_returns(self, return_data, company):
        """Create or update the given returns without archiving the others."""
        if isinstance(return_data, dict):
            return_data = [return_data]
        codes = [record.get("id") for record in return_data]
        existing = self.with_context(active_test=False).search(
            [("company_id", "=", company.id), ("sendcloud_code", "in", codes)]
        )
        existing_map = {record.sendcloud_code: record for record in existing}
        records = self.browse()
        vals_list = []
        for record_data in return_data:
            vals = self._prepare_sendcloud_return_from_response(record_data)
            vals["active"] = True
            record = existing_map.get(record_data.get("id"))
            if record:
                record.write(vals)
                records |= record
            else:
                vals["company_id"] = company.id
                vals_list += [vals]
        records |= self.create(vals_list)
        return records

    @api.model
    def sendcloud_create_or_update_returns(self, return_data, company):
        records = self._sendcloud_upsert_returns(return_data, company)
        if self.env.context.get("sendcloud_full_return_sync"):
            stale = company.sendcloud_return_ids - records
            stale.write({"active": False})
        records._create_odoo_returns()
        return records

    @api.model
    def sendcloud_sync_returns(self):
        return super(
            SendcloudReturn, self.with_context(sendcloud_full_return_sync=True)
        ).sendcloud_sync_returns()

    @api.model
    def _sendcloud_sync_return_code(self, sendcloud_code, company):
        """Fetch a single return from Sendcloud and upsert it."""
        integration = company.sendcloud_default_integration_id
        if not integration:
            return self.browse()
        return_data = integration.get_return(sendcloud_code)
        if not return_data:
            return self.browse()
        records = self._sendcloud_upsert_returns(return_data, company)
        records._create_odoo_returns()
        return records

    def action_create_odoo_return(self):
        self._create_odoo_returns(force=True)
        for record in self.filtered("picking_id"):
            record._link_sendcloud_shipment(
                record.picking_id, record._get_incoming_parcel()
            )

    def _create_odoo_returns(self, force=False):
        todo = self.filtered(
            lambda r: not r.picking_id and (force or r._is_within_return_start_date())
        )
        for record in todo:
            record_su = record.with_user(SUPERUSER_ID)
            try:
                with self.env.cr.savepoint():
                    record_su._create_odoo_return()
            except Exception as error:  # pylint: disable=broad-except
                record_su.odoo_return_error = str(error)
                _logger.exception(
                    "Sendcloud: could not create the Odoo return for %s",
                    record.sendcloud_code,
                )

    def _create_odoo_return(self):
        self.ensure_one()
        original = self._find_original_picking()
        self.original_picking_id = original
        if not original:
            self.odoo_return_error = self.env._(
                "No delivery could be matched to this return."
            )
            return self.env["stock.picking"]
        parcel = self._get_incoming_parcel()
        adopted = self._find_existing_return_operation(parcel)
        if adopted:
            self.picking_id = adopted
            self.original_picking_id = adopted.return_id
            self.odoo_return_error = False
            return adopted
        if parcel._sendcloud_is_cancelled():
            self.odoo_return_error = self.env._(
                "This return is cancelled at Sendcloud."
            )
            return self.env["stock.picking"]
        items = parcel.parcel_item_ids
        if not items:
            self.odoo_return_error = self.env._(
                "Sendcloud did not report any item for this return."
            )
            return self.env["stock.picking"]
        matched, unmatched = self._match_items_to_moves(original, items)
        picking = self._run_return_wizard(original, matched, unmatched)
        self.picking_id = picking
        self.odoo_return_error = False
        self._link_sendcloud_shipment(picking, parcel)
        self._post_return_details(picking, items)
        return picking

    def _get_created_date(self):
        """Creation date of the return at Sendcloud."""
        self.ensure_one()
        if not self.created_at:
            return False
        try:
            return isoparse(self.created_at).date()
        except (TypeError, ValueError):
            _logger.warning(
                "Sendcloud: unreadable creation date %r on return %s",
                self.created_at,
                self.sendcloud_code,
            )
            return False

    def _is_within_return_start_date(self):
        """Whether the return was created on or after the configured start date."""
        self.ensure_one()
        start_date = self.company_id.sendcloud_return_picking_start_date
        if not start_date:
            return True
        created_date = self._get_created_date()
        if not created_date:
            return True
        return created_date >= start_date

    def _find_original_picking(self):
        """Resolve the delivery this return refers to."""
        self.ensure_one()
        picking = self.outgoing_parcel_id.picking_id
        if picking:
            return picking
        order_number = (
            self.outgoing_parcel_order_number or self.incoming_parcel_order_number
        )
        if not order_number:
            return self.env["stock.picking"]
        order = self.env["sale.order"].search(
            [("name", "=", order_number), ("company_id", "=", self.company_id.id)],
            limit=1,
        )
        candidates = order.picking_ids.filtered(
            lambda p: p.picking_type_id.code == "outgoing" and p.state == "done"
        )
        return candidates.sorted("date_done")[-1:]

    def _get_incoming_parcel(self):
        """Incoming parcel of the return, with its items fetched from Sendcloud."""
        self.ensure_one()
        parcel = self.incoming_parcel_id
        if parcel.parcel_item_ids:
            return parcel
        if not self.incoming_parcel_code:
            return parcel
        integration = self.company_id.sendcloud_default_integration_id
        if not integration:
            return parcel
        parcel_data = integration.get_parcel(self.incoming_parcel_code)
        return self.env["sendcloud.parcel"].sendcloud_create_update_parcels(
            [parcel_data], self.company_id.id
        )

    def _find_existing_return_operation(self, parcel):
        """Return operation already linked to the incoming parcel."""
        self.ensure_one()
        picking = parcel.picking_id
        if picking and picking.picking_type_id.code == "incoming":
            return picking
        return self.env["stock.picking"]

    def _link_sendcloud_shipment(self, picking, parcel):
        """Carry the return shipping method, its tracking reference and the parcel."""
        self.ensure_one()
        if parcel and not parcel.picking_id:
            parcel.picking_id = picking
        parcel._sendcloud_sync_return_picking()
        if self.incoming_parcel_tracking_number and not picking.carrier_tracking_ref:
            picking.with_context(
                skip_sync_picking_to_sendcloud=True
            ).carrier_tracking_ref = self.incoming_parcel_tracking_number

    def _match_items_to_moves(self, original, items):
        """Match returned items against the moves of the original delivery by SKU."""
        self.ensure_one()
        moves = original.move_ids.filtered(lambda m: m.state == "done")
        matched = []
        unmatched = []
        for item in items:
            move = self.env["stock.move"]
            if item.sku:
                move = moves.filtered(
                    lambda m, sku=item.sku: m.product_id.default_code == sku
                )[:1]
            if not move and item.description:
                move = moves.filtered(
                    lambda m, name=item.description: m.product_id.display_name == name
                )[:1]
            if move:
                matched += [(item, move)]
            else:
                unmatched += [item]
        return matched, unmatched

    def _get_unidentified_product(self):
        return self.env.ref(
            "delivery_sendcloud_oca_return_portal.product_sendcloud_unidentified_return"
        )

    def _run_return_wizard(self, original, matched, unmatched):
        self.ensure_one()
        unidentified = self._get_unidentified_product()
        lines = [
            Command.create(
                {
                    "product_id": move.product_id.id,
                    "move_id": move.id,
                    "quantity": item.quantity,
                }
            )
            for item, move in matched
        ]
        lines += [
            Command.create({"product_id": unidentified.id, "quantity": item.quantity})
            for item in unmatched
        ]
        wizard = self.env["stock.return.picking"].create(
            {"picking_id": original.id, "product_return_moves": lines}
        )
        picking = wizard._create_return()
        self._describe_unidentified_moves(picking, unmatched)
        return picking

    def _describe_unidentified_moves(self, picking, unmatched):
        """Copy the Sendcloud description onto the moves of unidentified items."""
        if not unmatched:
            return
        unidentified = self._get_unidentified_product()
        moves = picking.move_ids.filtered(
            lambda m: m.product_id == unidentified
        ).sorted("id")
        for move, item in zip(moves, unmatched, strict=False):
            move.description_picking = item.description

    def _post_return_details(self, picking, items):
        self.ensure_one()
        body = self.env._(
            "Return %(code)s created from the Sendcloud return portal.",
            code=self.sendcloud_code,
        )
        details = []
        if self.status_display:
            details += [self.env._("Status: %(status)s", status=self.status_display)]
        if self.delivery_option:
            details += [
                self.env._(
                    "Delivery option: %(option)s",
                    option=dict(
                        self._fields["delivery_option"]._description_selection(self.env)
                    ).get(self.delivery_option),
                )
            ]
        if self.refund_type:
            details += [self.env._("Refund type: %(refund)s", refund=self.refund_type)]
        if self.message:
            details += [
                self.env._("Customer message: %(message)s", message=self.message)
            ]
        for item in items.filtered("return_message"):
            details += [
                self.env._(
                    "%(item)s: %(message)s",
                    item=item.description,
                    message=item.return_message,
                )
            ]
        picking.message_post(body=Markup("<br/>").join([body] + details))
