# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from ..postlogistics.web_service import DISALLOWED_CHARS
from .common import TestPostlogisticsCommon


class TestSanitizeValues(TestPostlogisticsCommon):
    """Just create records full of disallowed chars, an test that everyone of them
    is correctly removed, as none of those chars should be sent on postlogistics api.
    """

    @classmethod
    def setUpPartner(cls):
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "P<o\\t|at>o",
                "mobile": "+33123456789>",
                "phone": ">+33123456789<",
                "email": "w<>|\\hatever@whatever.too",
                "street": "42\\|<>whateverstraße",
                "street2": "42\\|<>whateverstraße",
                "zip": "43123\\",
                "city": "Mouais\\<>|",
            }
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpPartner()
        cls.picking = cls.create_picking(cls.partner)

    def check_strings_in_dict(self, values):
        # Do not check other types than strings.
        # Dict values are individually tested, no recursion here.
        values_to_check = [value for value in values.values() if isinstance(value, str)]
        self.check_strings_in_list(values_to_check)

    def check_strings_in_list(self, values):
        for value in values:
            self.assertFalse(any(char in value for char in DISALLOWED_CHARS))

    def test_sanitize(self):
        customer = self.service_class._prepare_customer(self.picking)
        self.check_strings_in_dict(customer)
        recipient = self.service_class._prepare_recipient(self.picking)
        self.check_strings_in_dict(recipient)
        packages = self.picking._get_packages_from_picking()
        item_list = self.service_class._prepare_item_list(
            self.picking, recipient, packages
        )
        self.check_strings_in_list(item_list)
        attributes = self.service_class._prepare_attributes(
            self.picking, packages, 1, 1
        )
        self.check_strings_in_dict(attributes)
