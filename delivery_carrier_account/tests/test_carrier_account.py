# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestCarrierAccount(TransactionCase):
    def test_get_carrier_account(self):
        """Test finding the correct account for a picking"""
        account = self.env["carrier.account"].create(
            {
                "name": "Account",
                "account": "account",
                "password": "password",
                "delivery_type": "base_on_rule",
                "sequence": 1,
            }
        )
        carrier = self.env.ref("delivery.delivery_carrier")
        carrier.write({"carrier_account_id": account.id})
        pick = self.env["stock.picking"].new(
            dict(
                carrier_id=carrier.id,
                company_id=self.env.user.company_id.id,
            )
        )

        picking_account = pick._get_carrier_account()
        self.assertEqual(picking_account, account)
