# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestCarrierAgency(BaseCommon):
    def test_get_carrier_agency(self):
        """Test finding the correct account for a picking"""
        san_fransico_wh = self.env.ref("stock.warehouse0")
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        chicago_wh = self.env["stock.warehouse"].create(
            {
                "name": "Chicago 1",
                "code": "CHIC1",
                "partner_id": partner.id,
            }
        )
        agency_chicago = self.env["delivery.carrier.agency"].create(
            {
                "name": "Normal Carrier Chicago agency",
                "delivery_type": "base_on_rule",
                "warehouse_ids": [Command.set(chicago_wh.ids)],
            }
        )
        agency_san_fransisco = self.env["delivery.carrier.agency"].create(
            {
                "name": "Normal Carrier San Fransisco agency",
                "delivery_type": "base_on_rule",
                "warehouse_ids": [Command.set(san_fransico_wh.ids)],
            }
        )
        product = self.env["product.product"].create(
            {"name": "Test Product", "type": "service"}
        )
        carrier = self.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "base_on_rule",
                "product_id": product.id,
            }
        )
        san_fransisco_picking = self.env["stock.picking"].new(
            dict(
                carrier_id=carrier.id,
                company_id=self.env.user.company_id.id,
                location_id=san_fransico_wh.lot_stock_id.id,
            )
        )
        agency = san_fransisco_picking._get_carrier_agency()
        self.assertEqual(agency, agency_san_fransisco)

        chicago_picking = self.env["stock.picking"].new(
            dict(
                carrier_id=carrier.id,
                company_id=self.env.user.company_id.id,
                location_id=chicago_wh.lot_stock_id.id,
            )
        )
        agency = chicago_picking._get_carrier_agency()
        self.assertEqual(agency, agency_chicago)
