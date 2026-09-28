# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.exceptions import UserError
from odoo.fields import Date


class DeliveryDachserManifiestoWizard(models.TransientModel):
    _name = "dachser.manifest.wizard"
    _description = "Get the Dachser Manifest for the given dates"

    date_from = fields.Date(
        required=True,
        default=fields.Date.context_today,
    )
    date_to = fields.Date()
    carrier_id = fields.Many2one(
        string="Carrier",
        required=True,
        comodel_name="delivery.carrier",
        domain=[("delivery_type", "=", "dachser")],
    )

    def get_manifest(self):
        """List of shippings for the given dates"""
        date_from = Date.to_string(self.date_from)
        date_to = Date.to_string(self.date_to) if self.date_to else ""
        manifest_data = []
        items = self.carrier_id.dachser_list_shippings(date_from, date_to)
        if not items:
            raise UserError(
                self.env._(
                    "It wasn't possible to get the manifest. Maybe there aren't "
                    "pickings for the selected date(s)."
                )
            )
        picking_model = self.env["stock.picking"]
        for item in items:
            ref = item["id"]
            picking = picking_model.search(
                [
                    ("carrier_id", "=", self.carrier_id.id),
                    ("carrier_tracking_ref", "=", ref),
                ],
                limit=1,
            )
            if not picking:
                raise UserError(
                    self.env._("No picking has been found with the reference %s") % ref,
                )
            manifest_data.append(
                {
                    "carrier_tracking_ref": picking.carrier_tracking_ref,
                    "reference": (
                        picking.sudo().sale_id.client_order_ref
                        or picking.sudo().sale_id.name
                        or ""
                    ),
                    "note": picking.note[:25] + "..." if picking.note else "",
                    "date": picking.scheduled_date.date(),
                    "partner": picking.partner_id.name or "",
                    "zip": picking.partner_id.zip or "",
                    "address": (
                        picking.partner_id.street
                        + " "
                        + (picking.partner_id.street2 or "")
                    ),
                    "city": picking.partner_id.city or "",
                    "state": picking.partner_id.state_id.name or "",
                    "number_of_packages": picking.number_of_packages,
                    "weight": picking.weight or "0",
                }
            )
        datas = {
            "ids": self.env.context.get("active_ids", []),
            "deliveries": manifest_data,
            "model": self._name,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "company_name": self.env.company.name,
        }
        return (
            self.env.ref("delivery_dachser.dachser_manifest_report")
            .with_context(landscape=True)
            .report_action(self, data=datas)
        )
