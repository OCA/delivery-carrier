# coding: utf-8
# Copyright 2021 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError

from .common import TestPackageConstraintCommon


def vals(vals_1, vals_2):
    result = vals_1.copy()
    result.update(vals_2)
    return result


class TestPackageConstraints(TestPackageConstraintCommon):
    def test_constraints(self):
        weight_heavy = self.max_weight + 1
        weight_light = self.max_weight - 1
        vals_packaging = {"packaging_id": self.packaging.id}
        vals_heavy = {"name": "H", "shipping_weight": weight_heavy}
        vals_light = {"name": "L", "shipping_weight": weight_light}

        package_heavy = self.package_model.create(vals_heavy)
        with self.assertRaises(ValidationError):
            package_heavy.packaging_id = self.packaging

        vals_wrong_create = vals(vals_heavy, vals_packaging)
        with self.assertRaises(ValidationError):
            self.package_model.create(vals_wrong_create)

        # this should work as expected
        package_light = self.package_model.create(vals(vals_light, vals_packaging))
        self.assertEqual(package_light.packaging_id.max_weight, self.max_weight)
