# Copyright 2012-2015 Akretion <http://www.akretion.com>.
# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_shipping_label_values(self, label):
        self.ensure_one()
        return {
            "name": label["name"],
            "res_id": self.id,
            "res_model": "stock.picking",
            "datas": label["file"],
            "file_type": label["file_type"],
            "package_id": label.get("package_id", False),
        }

    def attach_shipping_label(self, label):
        """Attach a label returned by send_to_shipper to a picking"""
        self.ensure_one()
        data = self.get_shipping_label_values(label)
        context_attachment = self.env.context.copy()
        # remove default_type setted for stock_picking
        # as it would try to define default value of attachement
        if "default_type" in context_attachment:
            del context_attachment["default_type"]
        return (
            self.env["shipping.label"].with_context(**context_attachment).create(data)
        )

    def _check_existing_shipping_label(self):
        """Check that labels don't already exist for this picking"""
        self.ensure_one()
        labels = self.env["shipping.label"].search(
            [("res_id", "=", self.id), ("res_model", "=", "stock.picking")]
        )
        if labels:
            raise UserError(
                _(
                    "Some labels already exist for the picking %s.\n"
                    "Please delete the existing labels in the "
                    "attachments of this picking and try again"
                )
                % self.name
            )
