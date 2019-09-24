# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.tests import TransactionCase
from openerp import exceptions
from mock import patch, Mock

MOCK_COSTCENTER = Mock()
MOCK_COSTCENTER.json.return_value = [{
    'value': '{"code": "123", "description": "test", "isDefault": "true"}',
    'nr': 1,
}]
MOCK_SERVICELEVEL_OTHERS = Mock()
MOCK_SERVICELEVEL_OTHERS.json.return_value = [{
    'value': '{"code": "123", "description": "test", "isDefault": "true"}',
    'nr': 1,
}]
MOCK_SERVICELEVEL_TIME = Mock()
MOCK_SERVICELEVEL_TIME.json.return_value = [{
    'value': '{"code": "123", "description": "test", "isDefault": "true"}',
    'nr': 1,
}]
MOCK_PACKAGE = Mock()
MOCK_PACKAGE.json.return_value = [{
    'value': '{'
             '"package": "true", "code": "123", "description": "test", '
             '"isDefault": "true", "type": "BOX", "length": 1, "width": 1, '
             '"height": 1, "weight": 1'
             '}',
    'nr': 1,
}]
MOCK_CARRIER = Mock()
MOCK_CARRIER.json.return_value = [{
    'value': '{'
             '"code": "123", "description": "test", "isDefault": "true", '
             '"name": "DHL"'
             '}',
    'nr': 1,
}]
MOCK_BOOKING_PROFILE = Mock()
MOCK_BOOKING_PROFILE.json.return_value = [{
    'value': '{'
             '"code": "123", "description": "test", "carrier": "123", '
             '"serviceLevelTime": "123", "serviceLevelOther": "123", '
             '"incoterms": "DAP", "costCenter": "123", "mailType": "1"'
             '}',
    'nr': 1,
}]

DATA = {
    'costcenter': MOCK_COSTCENTER,
    'servicelevel_others': MOCK_SERVICELEVEL_OTHERS,
    'servicelevel_time': MOCK_SERVICELEVEL_TIME,
    'packages': MOCK_PACKAGE,
    'carrier': MOCK_CARRIER,
    'bookingprofiles': MOCK_BOOKING_PROFILE,
}


def get_connection():
    """ Mock a connection to transsmart.
    """
    connection = Mock()
    mock_connected = Mock()
    mock_account = Mock()
    mock_account.retrieve_costcenter.return_value = DATA['costcenter']
    mock_account.retrieve_servicelevel_others.return_value = DATA[
        'servicelevel_others']
    mock_account.retrieve_servicelevel_time.return_value = DATA[
        'servicelevel_time']
    mock_account.retrieve_packages.return_value = DATA['packages']
    mock_account.retrieve_carrier.return_value = DATA['carrier']
    mock_account.retrieve_bookingprofiles.return_value = DATA[
        'bookingprofiles']
    mock_connected.Account = mock_account
    mock_shipment = Mock()
    response_shipment = Mock()
    response_shipment.ok = True
    response_shipment.json.return_value = [{'price': 1, 'trackingUrl': 'test'}]
    mock_shipment.book.return_value = response_shipment
    mock_connected.Shipment = mock_shipment
    connection.connect.return_value = mock_connected
    return connection


@patch(
    'openerp.addons.delivery_transsmart.models.'
    'transsmart_config_settings.Connection',
    new=get_connection,
    )
@patch(
    'openerp.addons.delivery_transsmart.models.'
    'stock_picking.Connection',
    new=get_connection,
    )
class TestTranssmart(TransactionCase):
    """ The sending of an picking order to transsmart is tested here,
    here is the test workflow:
    1) Create customer, product
    2) Create a stock picking
    3) Send it to transsmart and verify that there were no errors

    The setting of the scenario above will happen in the setup and the cases
    in the rest of the functions.
    """

    post_install = True
    at_install = False

    def setUp(self):
        """ Setting up the test environment.
        1) Synchronize with transsmart
        2) Create a customer
        3) Create a product of type `stock`.
        4) Create a picking of type `outgoing` with the appropriate values
        needed in order for the picking to be sent successfully the first time.
        5) Make sure that the company is transsmart_enabled
        """
        super(TestTranssmart, self).setUp()
        company_id = self.env['res.company'].search([], limit=1)
        country_id = self.env.ref('base.de')
        state_id = self.env['res.country.state'].create({
            'country_id': country_id.id,
            'name': 'test',
            'code': 123,
        })
        company_id.write({
            'street': 'street',
            'street2': 'street2',
            'zip': 123,
            'city': 'Berlin',
            'state_id': state_id.id,
            'country_id': country_id.id,
            'email': 'test@example.com',
            'phone': 1234,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'customer',
            'customer': True,
            'street': 'test',
            'street2': 'test',
            'zip': 123,
            'city': 'Berlin',
            'state_id': state_id.id,
            'country_id': country_id.id,
            'phone': 1234,
            'email': 'test@example.com',
        })
        self.product = self.env['product.product'].create({
            'name': 'product',
            'type': 'product',
        })
        type_out = self.env['stock.picking.type'].search(
            [('code', '=', 'outgoing')],
            limit=1,
        )
        self.order = self.env['stock.picking'].create({
            'partner_id': self.customer.id,
            'picking_type_id': type_out.id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'product_uom': self.env.ref(
                        'product.product_uom_categ_unit').id,
                    'name': 'product',
                    'location_id': self.env.ref('stock.warehouse0').id,
                    'location_dest_id': self.env.ref('stock.warehouse0').id
                    })
                ],
        })

    def verify_no_sync(self):
        """ Verify that there is no transsmart related data on the system
        before synchronization.
        """
        costcenters = self.env['cost.center'].search_count([])
        serviceleveltime = self.env['service.level.time'].search_count([])
        servicelevelother = self.env['service.level.other'].search_count([])
        packages = self.env['product.template'].search_count([
            ('package', '=', True)])
        carriers = self.env['res.partner'].search_count([
            ('carrier', '=', True)])
        bookingprofiles = self.env['booking.profile'].search_count([])
        self.assertFalse(costcenters)
        self.assertFalse(serviceleveltime)
        self.assertFalse(servicelevelother)
        self.assertFalse(packages)
        self.assertFalse(carriers)
        self.assertFalse(bookingprofiles)

    def test_synchronize(self):
        """ Perform a mock syncronization between Odoo and Transsmart and fill
        the models with dummy data.
        """
        self.verify_no_sync()
        settings = self.env['transsmart.config.settings'].create({
            'demo': True,
            'username': 'username',
            'password': 'password',
            'account_code': 'code',
        })
        settings.set_transsmart_defaults()
        settings.synchronize_models()
        booking_profile_id = self.env['booking.profile'].search(
            [],
            limit=1,
        )
        service_level_time_id = self.env['service.level.time'].search(
            [],
            limit=1,
        )
        service_level_other_id = self.env['service.level.other'].search(
            [],
            limit=1,
        )
        package_type_id = self.env['product.template'].search(
            [('package', '=', True)],
            limit=1,
        )
        self.order.write({
            'booking_profile_id': booking_profile_id.id,
            'service_level_time_id': service_level_time_id.id,
            'service_level_other_id': service_level_other_id.id,
            'package_type_id': package_type_id.id,
        })
        self.verify_sync()
        self.order.action_create_transsmart_document()

    def verify_sync(self):
        """ Verify that the data to be syncronized is fetched and inserted on
        the system
        """
        costcenters = self.env['cost.center'].search_count([])
        serviceleveltime = self.env['service.level.time'].search_count([])
        servicelevelother = self.env['service.level.other'].search_count([])
        packages = self.env['product.template'].search_count([
            ('package', '=', True)])
        carriers = self.env['res.partner'].search_count([
            ('carrier', '=', True)])
        bookingprofiles = self.env['booking.profile'].search_count([])
        self.assertTrue(costcenters)
        self.assertTrue(serviceleveltime)
        self.assertTrue(servicelevelother)
        self.assertTrue(packages)
        self.assertTrue(carriers)
        self.assertTrue(bookingprofiles)

    def test_send_to_transsmart_errors(self):
        """ Try to send the order to transsmart.
        Try sending it without filling in the neccessary fields, see
        if our local implementation stops you from doing so.
        """
        with self.assertRaises(exceptions.ValidationError):
            self.order.write({
                'service': None,
                'service_level_time_id': None,
                'service_level_other_id': None,
            })
            self.order.action_create_transsmart_document()
