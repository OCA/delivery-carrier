# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .test_delivery_carrier_label_ups import DeliveryCarrierLabelUpsCase


class InvoiceLineDataUps(DeliveryCarrierLabelUpsCase):

    def _partner_data(self):
        """ Set Canada as destination country """
        result = super()._partner_data()
        result["country_id"] = self.env.ref("base.ca").id
        return result

    def _order_line_data(self):
        """ Set order line quantity to 3 and add another line. """
        result = super()._order_line_data()
        result[0]["product_uom_qty"] = 3
        new_product = self.env["product.product"].create({
            "name": "Test product2",
            "type": "product",
            "standard_price": 7.0,
            "lst_price": 10.0,
        })
        result.append({
            "product_id": new_product.id,
            "product_uom_qty": 2,
        })
        return result

    def _product_data(self):
        """ Set a price for product to be shipped """
        result = super()._product_data()
        if result["name"] == "Carrier test product":
            result["standard_price"] = 100.0
            result["lst_price"] = 123.4
        return result

    def test_invoice_line_total(self):
        """ InvoiceLineTotal is Required for forward shipments
        whose origin is the US and destination is Puerto Rico or Canada.
        """

        # in the order check the product price
        order_line_product = self.order.order_line.mapped("product_id").filtered(
            lambda p: p.name == "Carrier test product")
        self.assertEqual(len(order_line_product), 1)
        self.assertEqual(order_line_product.standard_price, 100.0)
        self.assertEqual(order_line_product.lst_price, 123.4)

        # check from/to countries
        self.assertEqual(self.picking.partner_id.country_id.code, "CA")
        warehouse = self.picking.picking_type_id.warehouse_id
        self.assertEqual(warehouse.company_id.partner_id.country_id.code, "US")

        # check payload (InvoiceLineTotal is present)
        shipping_data = self.picking._ups_shipping_data()['ShipmentRequest']
        ship_from_address = shipping_data['Shipment']['ShipFrom']['Address']
        self.assertEqual(ship_from_address['CountryCode'], "US")
        ship_to_address = shipping_data['Shipment']['ShipTo']['Address']
        self.assertEqual(ship_to_address['CountryCode'], "CA")
        invoice_line_total = shipping_data['Shipment']['InvoiceLineTotal']
        self.assertEqual(invoice_line_total['CurrencyCode'], "USD")
        self.assertEqual(invoice_line_total['MonetaryValue'], "390.2")
