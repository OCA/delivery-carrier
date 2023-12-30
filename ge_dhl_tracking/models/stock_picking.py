from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_state = fields.Selection(
        selection_add=[("multiple_states", "Multiple States")]
    )

    def test_function(self):
        for record in self:
            record.carrier_id.dhl_parcel_de_provider_get_tracking_link(record)

    def action_see_dhl_tracking_event_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "ge_dhl_tracking.action_tracking_event"
        )
        tracking_ids = self.move_line_ids.mapped("result_package_id.tracking_id")
        action["domain"] = [("piece_code", "in", tracking_ids)]
        return action

    def get_tracking_ids(self):
        self.ensure_one()
        if self.carrier_tracking_ref:
            return self.carrier_tracking_ref.split(",")
