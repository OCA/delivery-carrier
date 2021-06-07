# coding: utf-8
# Copyright 2021 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError

from .common import TestGLS

gls_required_fields = [
    "gls_contact_id",
    "gls_login",
    "gls_password",
    "gls_url_tracking",
    "gls_url_test",
]


class TestCarrierConstraints(TestGLS):
    def test_missing_field(self):
        for field in gls_required_fields:
            values = self._get_gls_carrier_vals()
            values.pop(field)
            with self.assertRaises(ValidationError):
                self.env["delivery.carrier"].create(values)

    def test_tracking_url(self):
        """Check that we have a string formatting parameter"""
        values = self._get_gls_carrier_vals()
        values["gls_url_tracking"] = "https://gls-group.eu/EU/en/parcel-tracking/"
        with self.assertRaises(ValidationError):
            self.env["delivery.carrier"].create(values)

    def test_url_prod(self):
        values = self._get_gls_carrier_vals()
        values["prod_environment"] = True  # gls_url is already missing
        with self.assertRaises(ValidationError):
            self.env["delivery.carrier"].create(values)

    def test_cannot_modify_with_gls_parameters(self):
        values = self._get_gls_carrier_vals()
        gls_carrier = self.env["delivery.carrier"].create(values)
        vals_fixed = {"delivery_type": "fixed"}
        with self.assertRaises(ValidationError):
            gls_carrier.write(vals_fixed)

        # this works, as expected:
        vals_write = {field: False for field in gls_required_fields}
        vals_write.update(vals_fixed)
        gls_carrier.write(vals_write)

    def test_cannot_create_with_gls_parameters(self):
        values = self._get_gls_carrier_vals()
        values["delivery_type"] = "fixed"
        with self.assertRaises(ValidationError):
            self.env["delivery.carrier"].create(values)

        # however this works, as expected
        self.env["delivery.carrier"].create({"name": "notGLS"})
