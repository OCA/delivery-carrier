from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase

EASYPOST_TEST_KEY = "EZTK52f7d94f77344a44854f45762f3a4a11QfNflQ9TqssKdvK5fdGuUw"
EASYPOST_PROD_KEY = "EZTK52f7d94f77344a44854f45762f3a4a11QfNflQ9TqssKdvK5fdGuUw"


@tagged("post_install", "-at_install")
class EasypostTestBaseCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Set company currency to USD to match EasyPost rates
        usd_currency = cls.env.ref("base.USD")
        cls.env.company.currency_id = usd_currency

        product_sudo = cls.env["product.product"]
        cls.company = cls.env["res.partner"].create(
            {
                "name": "Odoo SA",
                "street": "44 Wall Street",
                "street2": "Suite 603",
                "city": "New York",
                "zip": 10005,
                "state_id": cls.env.ref("base.state_us_27").id,
                "country_id": cls.env.ref("base.us").id,
                "phone": "+1 (929) 352-6366",
                "email": "",
                "website": "www.example.com",
            }
        )

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "The Jackson Group",
                "street": "1515 Main Street",
                "street2": "",
                "city": "Columbia",
                "phone": "+1 (929) 352-6364",
                "zip": 29201,
                "state_id": cls.env.ref("base.state_us_41").id,
                "country_id": cls.env.ref("base.us").id,
            }
        )

        conf = cls.env["ir.config_parameter"]
        conf.set_param("product.weight_in_lbs", "1")
        precision = cls.env.ref("product.decimal_stock_weight")
        precision.digits = 4
        cls.uom_lbs = cls.env.ref("uom.product_uom_lb")
        cls.uom_lbs.rounding = 0.0001
        cls.product = product_sudo.create(
            {
                "name": "Product1",
                "type": "consu",
                "weight": 3.0,
                "volume": 4.0,
            }
        )
        cls.delivery_product = product_sudo.create(
            {
                "name": "Easypost OCA Delivery",
                "type": "service",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )

        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "EASYPOST OCA",
                "delivery_type": "easypost_oca",
                "easypost_oca_test_api_key": EASYPOST_TEST_KEY,
                "easypost_oca_production_api_key": EASYPOST_PROD_KEY,
                "easypost_oca_label_file_type": "ZPL",
                "product_id": cls.delivery_product.id,
            }
        )

        cls.default_packaging = cls.env["stock.package.type"].create(
            {
                "name": "My Easypost OCA Box",
                "package_carrier_type": "easypost_oca",
                "max_weight": 100,
                "height": 0,
                "packaging_length": 0,
                "width": 0,
            }
        )

    def _create_sale_order(self, qty=1):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = qty
        sale = order_form.save()
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=sale.id,
                default_carrier_id=self.carrier.id,
            )
        ).save()
        delivery_wizard.button_confirm()
        sale.action_confirm()
        return sale

    def _put_in_pack(self, picking):
        wiz_action = picking.action_put_in_pack()
        self.assertEqual(
            wiz_action["res_model"],
            "choose.delivery.package",
            "Wrong wizard returned",
        )
        wiz = (
            self.env[wiz_action["res_model"]]
            .with_context(**wiz_action["context"])
            .create({"delivery_package_type_id": self.default_packaging.id})
        )
        wiz.action_put_in_pack()
