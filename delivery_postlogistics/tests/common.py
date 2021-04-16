# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import SavepointCase

from ..postlogistics.web_service import PostlogisticsWebService

ENDPOINT_URL = "https://wedecint.post.ch/"
CLIENT_ID = "XXX"
CLIENT_SECRET = "XXX"
LICENSE = "XXX"


class TestPostlogisticsCommon(SavepointCase):
    @classmethod
    def setUpClassLicense(cls):
        cls.license = cls.env["postlogistics.license"].create(
            {"name": "TEST", "number": LICENSE}
        )

    @classmethod
    def setUpClassCarrier(cls):
        shipping_product = cls.env["product.product"].create({"name": "Shipping"})
        option_model = cls.env["postlogistics.delivery.carrier.template.option"]
        partner_id = cls.env.ref("delivery_postlogistics.partner_postlogistics").id
        label_layout = option_model.create({"code": "A6", "partner_id": partner_id})
        output_format = option_model.create({"code": "PDF", "partner_id": partner_id})
        image_resolution = option_model.create(
            {"code": "600", "partner_id": partner_id}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Postlogistics",
                "delivery_type": "postlogistics",
                "product_id": shipping_product.id,
                "postlogistics_endpoint_url": ENDPOINT_URL,
                "postlogistics_client_id": CLIENT_ID,
                "postlogistics_client_secret": CLIENT_SECRET,
                "postlogistics_license_id": cls.license.id,
                "postlogistics_label_layout": label_layout.id,
                "postlogistics_output_format": output_format.id,
                "postlogistics_resolution": image_resolution.id,
            }
        )

    @classmethod
    def setUpClassPackaging(cls):
        cls.postlogistics_pd_packaging = cls.env["product.packaging"].create(
            {
                "name": "PRI-TEST",
                "package_carrier_type": "postlogistics",
                "shipper_package_code": "PRI, BLN",
            }
        )

    @classmethod
    def setUpClassUserCompany(cls):
        cls.env.user.company_id.write(
            {"street": "Rue de Lausanne 1", "zip": "1030", "city": "Bussigny"}
        )
        cls.env.user.company_id.partner_id.country_id = cls.env.ref("base.ch")
        cls.env.user.lang = "en_US"

    @classmethod
    def setUpClassLocation(cls):
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

    @classmethod
    def create_picking(cls, partner=None, product_matrix=None):
        packaging = cls.postlogistics_pd_packaging
        if not partner:
            partner = cls.env["res.partner"].create(
                {
                    "name": "Camptocamp SA",
                    "street": "EPFL Innovation Park, Bât A",
                    "zip": "1015",
                    "city": "Lausanne",
                }
            )
        picking = cls.env["stock.picking"].create(
            {
                "partner_id": partner.id,
                "carrier_id": cls.carrier.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
            }
        )
        if not product_matrix:
            product_matrix = [
                (cls.env["product.product"].create({"name": "Product A"}), 3),
            ]
        for product, qty in product_matrix:
            cls.env["stock.move"].create(
                {
                    "name": product.name,
                    "product_id": product.id,
                    "product_uom_qty": qty,
                    "product_uom": product.uom_id.id,
                    "picking_id": picking.id,
                    "location_id": cls.stock_location.id,
                    "location_dest_id": cls.customer_location.id,
                }
            )
        choose_delivery_package_wizard = cls.env["choose.delivery.package"].create(
            {"picking_id": picking.id, "delivery_packaging_id": packaging.id}
        )
        picking.action_assign()
        choose_delivery_package_wizard.put_in_pack()
        return picking

    @classmethod
    def setUpClassWebservice(cls):
        cls.service_class = PostlogisticsWebService(cls.env.user.company_id)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.setUpClassLicense()
        cls.setUpClassCarrier()
        cls.setUpClassPackaging()
        cls.setUpClassUserCompany()
        cls.setUpClassLocation()
        cls.setUpClassWebservice()
