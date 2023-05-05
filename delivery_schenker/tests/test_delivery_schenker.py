# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class TestDeliverySchenker(common.SavepointCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Schenker",
                "schenker_access_key": "key",
                "schenker_group_id": "group",
                "schenker_user": "user",
                "schenker_barcode_format": "A4",
                "schenker_barcode_mail": "test@test.com",
                "schenker_booking_type": "land",
                "schenker_incoterm_id": cls.env.ref("account.incoterm_EXW").id,
                "schenker_service_type": "D2D",
                "schenker_service_land": "CON",
                "schenker_indoor_delivery": True,
                "schenker_express": True,
                "schenker_food_related": True,
                "schenker_heated_transport": True,
                "schenker_home_delivery": True,
                "schenker_own_pickup": True,
                "schenker_pharmaceuticals": True,
                "schenker_default_packaging_id": cls.env.ref(
                    "delivery_schenker.schenker_packaging_01"
                ).id,
                "schenker_address_number": "address_number",
                "product_id": cls.env.ref("delivery.product_product_delivery").id,
            }
        )
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "country_id": cls.company.partner_id.country_id.id,
                "phone": cls.company.partner_id.phone,
                "email": "test@odoo.com",
                "street": cls.company.partner_id.street,
                "city": cls.company.partner_id.city,
                "zip": cls.company.partner_id.zip,
                "state_id": cls.company.partner_id.state_id.id,
                "vat": cls.company.partner_id.vat,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "type": "product",
                "weight": 1,
                "volume": 1,
            }
        )
        cls.sale, cls.picking = cls._create_sale_order(cls)
        cls._process_picking(cls, cls.picking)

    def _process_picking(self, picking):
        picking.move_lines.quantity_done = 1
        picking.button_validate()
        # Delete result package, otherwise Unittests will fail
        # because the addon base_delivery_carrier_label gets installed first
        # which creates a default package within the method _set_a_default_package
        picking.move_line_ids.result_package_id = False
        picking.date_done = "2023-05-04 00:00:00"

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
        sale = order_form.save()
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": sale.id, "default_carrier_id": self.carrier.id}
            )
        ).save()
        delivery_wizard.button_confirm()
        sale.action_confirm()
        return sale, sale.picking_ids

    def _prepare_schenker_shipping(self, picking, vals=None):
        vals = vals or {}
        res = {
            "barcodeRequest": "A4",
            "barcodeRequestEmail": "test@test.com",
            "start_pos": 1,
            "separated": False,
            "address": [
                {
                    "type": "SHIPPER",
                    "name1": "My Company (San Francisco)",
                    "locationType": "PHYSICAL",
                    "personType": "COMPANY",
                    "street": "250 Executive Park Blvd, Suite 3400",
                    "postalCode": "94134",
                    "city": "San Francisco",
                    "countryCode": "US",
                    "preferredLanguage": "en",
                    "email": "info@yourcompany.com",
                    "phone": "+1 (650) 555-0111 ",
                    "stateCode": "CA",
                    "stateName": "California",
                    "schenkerAddressId": "address_number",
                },
                {
                    "type": "CONSIGNEE",
                    "name1": "Test partner",
                    "locationType": "PHYSICAL",
                    "personType": "COMPANY",
                    "street": "250 Executive Park Blvd, Suite 3400",
                    "postalCode": "94134",
                    "city": "San Francisco",
                    "countryCode": "US",
                    "preferredLanguage": "en",
                    "email": "test@odoo.com",
                    "phone": "+1 (650) 555-0111 ",
                    "stateCode": "CA",
                    "stateName": "California",
                },
            ],
            "incoterm": "EXW",
            "incotermLocation": "Test partner",
            "productCode": "CON",
            "measurementType": "METRIC",
            "grossWeight": 1.0,
            "shippingInformation": {
                "shipmentPosition": [
                    {
                        "dgr": False,
                        "cargoDesc": picking.name,
                        "grossWeight": 1.0,
                        "volume": 1.0,
                        "packageType": "CI",
                        "stackable": False,
                        "pieces": 1,
                    }
                ],
                "grossWeight": 1.0,
                "volume": 1.0,
            },
            "measureUnit": "VOLUME",
            "customsClearance": False,
            "neutralShipping": False,
            "pickupDates": {
                "pickUpDateFrom": "2023-05-04T02:00:00+02:00",
                "pickUpDateTo": "2023-05-05T01:59:59+02:00",
            },
            "specialCargo": False,
            "specialCargoDescription": False,
            "serviceType": "D2D",
            "indoorDelivery": True,
            "express": True,
            "foodRelated": True,
            "heatedTransport": True,
            "homeDelivery": True,
            "ownPickup": True,
            "pharmaceuticals": True,
            "measureUnitVolume": 1.0,
        }
        res.update(vals)
        return res

    def test_delivery_schenker(self):
        vals = self.carrier._prepare_schenker_shipping(self.picking)
        self.assertDictEqual(self._prepare_schenker_shipping(self.picking), vals)

    def test_delivery_schenker_address_number(self):
        vals = self.carrier._prepare_schenker_shipping(self.picking)
        self.assertEqual(
            list(filter(lambda a: a["type"] == "SHIPPER", vals["address"]))[0][
                "schenkerAddressId"
            ],
            self.carrier.schenker_address_number,
        )
        self.carrier.schenker_partner_invoice_id = self.company.partner_id.id
        vals = self.carrier._prepare_schenker_shipping(self.picking)
        self.assertEqual(
            list(filter(lambda a: a["type"] == "INVOICE", vals["address"]))[0][
                "schenkerAddressId"
            ],
            self.carrier.schenker_address_number,
        )
        self.assertTrue(
            "schenkerAddressId"
            not in list(filter(lambda a: a["type"] == "SHIPPER", vals["address"]))[0]
        )
