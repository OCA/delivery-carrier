# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestCarrierAgency(TransactionCase):
    def test_get_carrier_agency(self):
        """Test finding the correct account for a picking"""
        chicago_wh = self.env.ref("stock.stock_warehouse_shop0")
        san_fransico_wh = self.env.ref("stock.warehouse0")
        agency_chicago = self.env["delivery.carrier.agency"].create(
            {
                "name": "Normal Carrier Chicago agency",
                "delivery_type": "fixed",
                "warehouse_ids": [(6, 0, chicago_wh.ids)],
            }
        )
        agency_san_fransisco = self.env["delivery.carrier.agency"].create(
            {
                "name": "Normal Carrier San Fransisco agency",
                "delivery_type": "fixed",
                "warehouse_ids": [(6, 0, san_fransico_wh.ids)],
            }
        )
        san_fransisco_picking = self.env["stock.picking"].new(
            dict(
                carrier_id=self.env.ref("delivery.normal_delivery_carrier").id,
                company_id=self.env.user.company_id.id,
                location_id=san_fransico_wh.lot_stock_id.id,
            )
        )
        agency = san_fransisco_picking._get_carrier_agency()
        self.assertEqual(agency, agency_san_fransisco)

        chicago_picking = self.env["stock.picking"].new(
            dict(
                carrier_id=self.env.ref("delivery.normal_delivery_carrier").id,
                company_id=self.env.user.company_id.id,
                location_id=chicago_wh.lot_stock_id.id,
            )
        )
        agency = chicago_picking._get_carrier_agency()
        self.assertEqual(agency, agency_chicago)
