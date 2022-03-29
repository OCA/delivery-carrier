# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

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
                "delivery_type": "fixed",
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
        carrier_id = self.env.ref("delivery.normal_delivery_carrier").id
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

    def test_attach_shipping_label(self):
        """Test if attaching labels works correctly"""
        picking = self.env["stock.picking"].new(
            dict(
                carrier_id=self.env.ref("delivery.normal_delivery_carrier").id,
                company_id=self.env.user.company_id.id,
            )
        )
        label = picking.with_context(
            # test if the function protect against an unwanted key in the context
            default_type="some_type",
        ).attach_shipping_label(
            dict(
                name="hello_world.pdf",
                file=base64.b64encode(bytes("hello world", "utf8")),
                file_type="pdf",
                package_id=self.env["stock.quant.package"]
                .create(dict(name="package"))
                .id,
                tracking_number="hello",
            )
        )
        self.assertEqual(label.name, "hello_world.pdf")

    def test_delivery_carrier_option(self):
        """Mandatory option on delivery options sets color"""
        option = self.env["delivery.carrier.option"].create(
            {
                "name": __name__,
                "code": __name__,
            }
        )
        self.assertFalse(option.color)
        option.mandatory = True
        self.assertEqual(option.color, 2)
