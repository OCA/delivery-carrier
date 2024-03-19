import base64

from odoo import models


# pylint: disable=consider-merging-classes-inherited
class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _get_base_delivery_carrier_labels(self, tracking_base):
        self.ensure_one()
        i = 1
        result = list()
        for package in self.move_line_ids.package_level_id.package_id:
            number = tracking_base + "-" + str(i)
            result.append(
                {
                    "package_id": package.id,
                    "tracking_number": number,
                    "name": number,
                    "file": base64.b64encode(b"test"),
                    "file_type": "zpl2",
                }
            )
            i += 1
        return result
