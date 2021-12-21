# Copyright 2016-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _, api, exceptions, fields, models


class PickingBatchApplyCarrier(models.TransientModel):
    _name = "picking.batch.apply.carrier"
    _description = "Picking Batch Apply Carrier"

    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", required=True)

    @api.multi
    def _check_domain(self, batch_ids):
        """A domain excluding the batches on which we don't allow
        to change the carrier.

        Can be overrided to change the domain.
        """
        return [("state", "!=", "done"), ("id", "in", batch_ids)]

    @api.multi
    def apply(self):
        self.ensure_one()
        batch_ids = self.env.context.get("active_ids")
        if not batch_ids:
            raise exceptions.UserError(_("No selected picking batch"))

        batch_obj = self.env["stock.picking.batch"]
        domain = self._check_domain(batch_ids)
        batchs = batch_obj.search(domain)
        batchs.write({"carrier_id": self.carrier_id.id})
        batchs.action_set_options()
        return {"type": "ir.actions.act_window_close"}
