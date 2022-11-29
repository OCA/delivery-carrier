# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestHelperFunctions(TransactionCase):
    """Test convenience functions on stock.picking"""

    def test_get_carrier_account(self):
        """Test finding the correct account for a picking"""
        account_without_company = self.env["carrier.account"].create(
            {
                "name": "Account without company",
                "account": "account",
                "password": "password",
                "delivery_type": "base_on_rule",
                "sequence": 1,
            }
        )
        account_with_company = account_without_company.copy(
            default=dict(
                name="Account with company",
                company_id=self.env.user.company_id.id,
                sequence=2,
            ),
        )
        second_account_with_company = account_with_company.copy(
            default=dict(name="2. Account with company", sequence=-1),
        )
        carrier_id = self.env.ref("delivery.delivery_carrier").id
        pick = self.env["stock.picking"].new(
            dict(
                carrier_id=carrier_id,
                company_id=self.env.user.company_id.id,
            )
        )

        account = pick._get_carrier_account()
        self.assertEqual(account, second_account_with_company)

        # restrict second_account_with_company to another delivery method
        free_method = self.env.ref("delivery.free_delivery_carrier")
        second_account_with_company.write({"carrier_ids": [(6, 0, [free_method.id])]})
        account = pick._get_carrier_account()
        self.assertEqual(account, account_with_company)

        second_account_with_company.write({"carrier_ids": [(4, carrier_id, 0)]})
        account = pick._get_carrier_account()
        self.assertEqual(account, second_account_with_company)
