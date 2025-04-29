# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from functools import reduce

from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _is_batch_roulier(self):
        # Check if the picking is part of a batch with a roulier carrier

        return (
            len(self.mapped("batch_id")) == 1
            and self.batch_id
            and self.batch_id.carrier_id
            and self.batch_id.carrier_id._is_roulier()
        )

    def send_to_shipper(self):
        if self._is_batch_roulier():
            # We are in a batch with a roulier carrier
            # We need to send unsent packages
            packages = self.package_ids - self.batch_id.sent_package_ids
            # Do not send packages that already have a tracking number
            packages = packages.filtered(lambda p: not p.parcel_tracking)
            if not packages:
                # Nothing to send
                return

            # First sanity checks
            # Check that all package pickings have the same sender/receiver:
            for package in packages:
                package_pickings = (
                    self.env["stock.move.line"]
                    .search(
                        [
                            "|",
                            ("result_package_id", "=", package.id),
                            ("package_id", "=", package.id),
                        ]
                    )
                    .mapped("picking_id")
                )

                # Set carrier on pickings
                package_pickings.write({"carrier_id": self.carrier_id.id})

                # Check sender/receiver uniformity
                for kind in ("sender", "receiver"):
                    addresses = reduce(
                        lambda x, y: x | y,
                        (
                            getattr(package_picking, f"_get_{kind}")()
                            or self.env["res.partner"]
                            for package_picking in package_pickings
                        ),
                    )
                    if not addresses:
                        raise UserError(
                            _(
                                "Can't determine %(kind)s address for pickings: %(pickings)s"
                            )
                            % {
                                "kind": kind,
                                "pickings": ", ".join(package_pickings.mapped("name")),
                            }
                        )
                    if len(addresses) > 1:
                        raise UserError(
                            _(
                                "Multiple %(kind)s addresses found for pickings: %(pickings)s"
                            )
                            % {
                                "kind": kind,
                                "pickings": ", ".join(package_pickings.mapped("name")),
                            }
                        )

            # Send packages
            res = self.batch_id.carrier_id.send_shipping(self)[0]
            # Mark packages as sent (for use in _roulier_generate_labels)
            self.batch_id.sent_package_ids |= packages
            # Update tracking number
            if res["tracking_number"]:
                self.batch_id.carrier_tracking_ref = ";".join(
                    [
                        tracking
                        for tracking in (
                            self.batch_id.carrier_tracking_ref,
                            res["tracking_number"],
                        )
                        if tracking
                    ]
                )
            return

        return super().send_to_shipper()

    def _send_confirmation_email(self):
        # Bypass odoo's foreach picking that prevents to call a single
        # send_to_shipper with all batch packages independently of the pickings
        if self._is_batch_roulier():
            self.sudo().send_to_shipper()

        # Call the super method to handle the email sending
        return super()._send_confirmation_email()

    def _roulier_generate_labels(self):
        if self._is_batch_roulier():
            label_info = []

            # Generate labels only for unsent packages
            packages = self.package_ids - self.batch_id.sent_package_ids
            # Do not send packages that already have a tracking number
            packages = packages.filtered(lambda p: not p.parcel_tracking)
            label_info.append(packages._generate_labels(self[0]))
            return label_info

        return super()._roulier_generate_labels()

    def get_shipping_label_values(self, label):
        self.ensure_one()
        if self._is_batch_roulier():
            # Attach the label to the batch instead of the picking
            return {
                "name": label["name"],
                "res_id": self.batch_id.id,
                "res_model": "stock.picking.batch",
                "datas": label["file"],
                "file_type": label["file_type"],
            }
        return super().get_shipping_label_values(label)
