# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.tests import common


SINGLE_OPTION_TYPES = [
    'label_layout',
    'output_format',
    'resolution',
]


class TestDelivery(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestDelivery, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.service_group = cls.env['postlogistics.service.group'].create({
            'name': "TEST SERVICE GROUP",
            'group_extid': 45879089,    # Random
        })
        cls.carrier = cls.env['delivery.carrier'].create({
            'name': "TEST CARRIER",
            'delivery_type': 'postlogistics',
            'product_id': cls.env.ref(
                'delivery_carrier_label_postlogistics.'
                'product_postlogistics_service').id,
            'postlogistics_service_group_id': cls.service_group.id,
        })
        cls.carrier_option = cls.create_carrier_option()

    @classmethod
    def create_carrier_option(cls, template=False, values=None):
        vals = {
            'name': "OPTION",
            # 'postlogistics_type': 'basic',
        }
        option_model = cls.env['delivery.carrier.option']
        if template:
            option_model = cls.env['delivery.carrier.template.option']
            vals['name'] = "TEMPLATE OPTION"
        if values:
            vals.update(values)
        return option_model.create(vals)

    def test_carrier_option_allowed_tmpl_options_ids_1(self):
        """Check allowed_tmpl_option_ids computed field when the carrier
        option has no carrier associated.
        """
        self.carrier_option.carrier_id = False
        self.assertEqual(
            self.carrier_option.allowed_tmpl_options_ids,
            self.carrier_option.carrier_id.allowed_tmpl_options_ids)

    def test_carrier_option_allowed_tmpl_options_ids_2(self):
        """Check allowed_tmpl_option_ids computed field when the carrier
        option has a carrier associated.
        """
        self.carrier_option.carrier_id = self.carrier
        self.assertEqual(
            self.carrier_option.allowed_tmpl_options_ids,
            self.carrier_option.carrier_id.allowed_tmpl_options_ids)

    def test_carrier_option_allowed_tmpl_options_ids_1_with_context(self):
        """Check allowed_tmpl_option_ids computed field + with_context
        when the carrier option has no carrier associated.
        """
        tmpl_options = self.env.ref(
            'delivery_carrier_label_postlogistics.'
            'postlogistics_layout_option_a6')
        carrier_option = self.carrier_option.with_context(
            default_allowed_tmpl_options_ids=tmpl_options.ids)
        self.assertEqual(
            carrier_option.allowed_tmpl_options_ids,
            tmpl_options)

    def test_carrier_option_allowed_tmpl_options_ids_1_with_context(self):
        """Check allowed_tmpl_option_ids computed field + with_context
        when the carrier option has a carrier associated.
        """
        tmpl_options = self.env.ref(
            'delivery_carrier_label_postlogistics.'
            'postlogistics_layout_option_a6')
        self.carrier_option.carrier_id = self.carrier
        carrier_option = self.carrier_option.with_context(
            default_allowed_tmpl_options_ids=tmpl_options.ids)
        # tmpl_options should be ignored as a carrier is defined on the option
        self.assertEqual(
            carrier_option.allowed_tmpl_options_ids,
            self.carrier_option.carrier_id.allowed_tmpl_options_ids)

    def test_carrier_postlogistics_basic_service_ids(self):
        self.assertFalse(self.carrier.postlogistics_basic_service_ids)

    def test_carrier_allowed_tmpl_options_ids_1(self):
        """Check allowed template options when there is no basic template
        option and no available option configured on the carrier.
        """
        services = self.env['delivery.carrier.template.option'].search(
            [('postlogistics_type', 'in', SINGLE_OPTION_TYPES)])
        self.assertEqual(
            self.carrier.allowed_tmpl_options_ids,
            services)

    def test_carrier_allowed_tmpl_options_ids_2(self):
        """Check allowed template options when there is no basic template
        option and one mandatory available option configured on the carrier.
        """
        self.carrier.available_option_ids += self.create_carrier_option(
            values={'postlogistics_type': 'resolution',
                    'mandatory': True,
                    'carrier_id': self.carrier.id})
        single_option_types = [x for x in SINGLE_OPTION_TYPES
                               if x != 'resolution']
        services = self.env['delivery.carrier.template.option'].search(
            [('postlogistics_type', 'in', single_option_types)])
        self.assertEqual(
            self.carrier.allowed_tmpl_options_ids,
            services)
