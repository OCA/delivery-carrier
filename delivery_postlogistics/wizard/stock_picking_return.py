from odoo import models


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _create_returns(self):
        new_picking, pick_type_id = super(ReturnPicking, self)._create_returns()
        if self.picking_id.delivery_type == "postlogistics":
            picking = self.env["stock.picking"].browse(new_picking)
            picking.write({"carrier_id": self.picking_id.carrier_id.id})
        return new_picking, pick_type_id
