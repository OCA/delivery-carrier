# coding: utf-8
# Copyright 2021 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestPackageConstraintCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPackageConstraintCommon, cls).setUpClass()

        cls.max_weight = 14
        vals_packaging = {"name": "Packaging14", "max_weight": cls.max_weight}
        cls.packaging = cls.env["product.packaging"].create(vals_packaging)
        cls.package_model = cls.env["stock.quant.package"]
