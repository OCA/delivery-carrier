from odoo import fields, models


class DeliveryCarrier(models.Model):

    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("test", "Test")], ondelete={"test": "cascade"}
    )


class StockPackageType(models.Model):

    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("test", "test")], ondelete={"test": "cascade"}
    )
