# Copyright 2024 Therp BV (<https://therp.nl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestSsccSequence(TransactionCase):
    def test_sscc_sequence(self):
        package_sequence = self.env.ref("stock.seq_quant_package")
        package_sequence.padding = 5
        package_sequence.prefix = None
        package_sequence.use_python_code = True
        package_sequence.python_code = (
            "'123456789012' + number_padded "
            "+ str(get_barcode_check_digit('123456789012' + number_padded + 'x'))"
        )

        package1 = self.env["stock.quant.package"].create({})
        sscc1 = package1.name
        _logger.info(sscc1)
        self.assertTrue(package1.valid_sscc)
        package2 = self.env["stock.quant.package"].create({})
        sscc2 = package2.name
        _logger.info(sscc2)
        self.assertTrue(package2.valid_sscc)
        self.assertNotEqual(sscc1, sscc2)
