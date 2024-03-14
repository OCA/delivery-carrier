#   Copyright (C) 2012-2014 Akretion France (www.akretion.com)
#   @author: David BEAL <david.beal@akretion.com>
#   @author: Sebastien BEAU <sebastien.beau@akretion.com>
#   @author: Chafique DELLI <chafique.delli@akretion.com>
#   @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models
from odoo.exceptions import UserError


class DeliveryDepositWizard(models.TransientModel):
    _name = "delivery.deposit.wizard"
    _description = "Wizard to create Deposit Slip"

    delivery_type = fields.Selection(
        selection=lambda self: self.env["delivery.carrier"]
        ._fields["delivery_type"]
        .selection,
        required=True,
        help="Delivery type (combines several delivery methods)",
    )

    def _prepare_deposit_slip(self):
        self.ensure_one()
        return {"delivery_type": self.delivery_type, "company_id": self.env.company.id}

    def _fetch_pickings(self):
        self.ensure_one()
        carriers = self.env["delivery.carrier"].search(
            [("delivery_type", "=", self.delivery_type)]
        )
        pickings = self.env["stock.picking"].search(
            [
                ("carrier_id", "in", carriers.ids),
                ("deposit_slip_id", "=", False),
                ("state", "=", "done"),
                ("picking_type_id.code", "!=", "incoming"),
            ]
        )
        return pickings

    def create_deposit_slip(self):
        self.ensure_one()
        pickings = self._fetch_pickings()
        if pickings:
            vals = self._prepare_deposit_slip()
            deposit = self.env["deposit.slip"].create(vals)
            pickings.write({"deposit_slip_id": deposit.id})
            action = {
                "name": "Deposit Slip",
                "type": "ir.actions.act_window",
                "res_model": "deposit.slip",
                "view_type": "form",
                "view_mode": "form,tree",
                "res_id": deposit.id,
                "nodestroy": False,
                "target": "current",
            }
            return action
        else:
            raise UserError(
                _(
                    "There are no delivery orders in transferred "
                    "state with a delivery method type '%s' "
                    "not already linked to a deposit slip."
                )
                % self.delivery_type
            )
