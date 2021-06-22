# coding: utf-8
# Copyright 2021 ACSONE SA/NV
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def joincat(s1, s2):
    """Simply append a ref to a string, or get the string itself if s1 is falsy."""
    return s2 if not s1 else ",".join((s1, s2))


class StockPicking(models.Model):
    _inherit = "stock.picking"

    gls_parcel_shop = fields.Char(
        "GLS Parcel Shop Identifier", help="Fill this for a delivery to a ParcelShop.",
    )
    gls_package_ref = fields.Char("GLS Package Identifiers", readonly=True, copy=False)

    def _check_is_everything_packaged(self):
        for picking in self:
            if not all(o.result_package_id for o in picking.pack_operation_product_ids):
                msg = _("For GLS every operation should be put in a pack.")
                raise ValidationError(msg)

    def do_transfer(self):
        """Check that each GLS picking has been completely sent."""
        gls_pickings = self.filtered(lambda p: p.delivery_type == "gls")
        gls_pickings._check_is_everything_packaged()
        return super(StockPicking, self).do_transfer()

    def gls_send_shipping(self, delivery_carrier=False):
        for package in self.mapped("pack_operation_product_ids.result_package_id"):
            if not package.parcel_tracking:
                self.gls_send_shipping_package(package)
        return self.carrier_tracking_ref

    def gls_send_shipping_package(self, package):
        self.ensure_one()
        package.carrier_id = self.carrier_id
        package.gls_picking_id = self
        package.gls_send_shipping_package()
        self.gls_package_ref = joincat(self.gls_package_ref, package.gls_package_ref)
        tracking = package.parcel_tracking
        self.carrier_tracking_ref = joincat(self.carrier_tracking_ref, tracking)
        return self.carrier_tracking_ref

    def generate_labels(self, package_ids=None):
        """Alias to gls_send_shipping, for compatibility with base_delivery."""
        return self.gls_send_shipping()

    def gls_cancel_shipment(self):
        for package in self.pack_operation_product_ids.result_package_id:
            if package.parcel_tracking:
                package.gls_cancel_shipment()

        self.carrier_tracking_ref = False
        self.gls_package_ref = False
