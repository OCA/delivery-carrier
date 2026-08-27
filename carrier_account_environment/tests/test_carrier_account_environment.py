# Copyright 2019 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base.tests.common import BaseCommon


class TestCarrierAccount(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier_account = cls.env["carrier.account"].create(
            {"name": "Test Carrier"}
        )

    def test_server_env_fields(self):
        """Test that _server_env_fields includes expected fields."""
        server_env_fields = self.carrier_account._server_env_fields
        self.assertIn("account", server_env_fields)
        self.assertIn("password", server_env_fields)

    def test_server_env_global_section_name(self):
        """Test that _server_env_global_section_name
        returns the correct section name."""
        self.assertEqual(
            self.carrier_account._server_env_global_section_name(), "carrier_account"
        )
