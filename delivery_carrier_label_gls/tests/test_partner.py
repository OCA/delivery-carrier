# coding: utf-8
# Copyright 2021 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError

from .common import TestGLS


class TestPartner(TestGLS):
    def test_belgian_zip(self):
        """Check that we have a string formatting parameter"""
        expected = "1367"
        self.partner.zip = "B-1367"
        iso_zip = self.partner._get_iso_zip(validate_raises=True)
        self.assertEqual(iso_zip, expected)
        self.partner.zip = "B-136"
        with self.assertRaises(ValidationError):
            self.partner._get_iso_zip(validate_raises=True)
