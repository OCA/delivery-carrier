from odoo import models


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _create_return(self):
        new_picking = super()._create_return()
        if self.picking_id.delivery_type == "postlogistics":
            new_picking.write({"carrier_id": self.picking_id.carrier_id.id})
        return new_picking
