# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError
from odoo.tools import mute_logger

from .common import TestPostlogisticsCommon, recorder


class TestApiReturnedErrors(TestPostlogisticsCommon):
    """Test reported errors from the PostLogistics API."""

    @mute_logger("odoo.addons.delivery_postlogistics.postlogistics.web_service")
    def test_generate_label_error_weight_over_limit(self):
        """Check generating a label for an overweight parcel.

        400 error with an empty body.
        """
        picking = self.create_picking(
            product_matrix=[
                (self.env["product.product"].create({"name": "Heavy Product"}), 1)
            ]
        )
        picking.move_line_ids.result_package_id.shipping_weight = 169.62
        with recorder.use_cassette(
            "test_generate_label_error_weight_over_limit",
            allow_playback_repeats=True,
        ):
            with self.assertRaises(UserError) as cm:
                picking.generate_postlogistics_shipping_labels()
        message = str(cm.exception)
        self.assertIn("PostLogistics error:", message)
        self.assertIn("HTTP 400", message)
        self.assertIn("no details from the API", message)

    @mute_logger("odoo.addons.delivery_postlogistics.postlogistics.web_service")
    def test_generate_label_error_with_body(self):
        """Check error with a json body: invalid franking license.

        400 error with json error.
        """
        picking = self.create_picking()
        with recorder.use_cassette(
            "test_generate_label_error_with_body", allow_playback_repeats=True
        ):
            with self.assertRaises(UserError) as cm:
                picking.generate_postlogistics_shipping_labels()
        message = str(cm.exception)
        self.assertIn("PostLogistics error:", message)
        self.assertIn("HTTP 400", message)
        self.assertIn('"field" : "frankingLicense"', message)
        self.assertIn('"error" : "Invalid"', message)
