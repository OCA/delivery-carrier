# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import json
import requests

from odoo import models, fields, api, _, exceptions


class PostlogisticsAuth(models.TransientModel):
    _name = 'postlogistics.auth'
    _description = 'Postlogistics Auth'

    authentication_url = fields.Char(
        string='Authentication url',
        default='https://wedecint.post.ch/WEDECOAuth/token',
        required=True,
    )

    generate_label_url = fields.Char(
        string='Generate label url',
        default='https://wedecint.post.ch/api/barcode/v1/generateAddressLabel',
        required=True,
    )

    # client_id and client_secret are only defined as required in the form view
    # to allow to reset them (into reset_access_token function)
    client_id = fields.Char(
        string='Client ID',
    )

    client_secret = fields.Char(
        string='Client Secret',
    )

    state = fields.Selection([
        ('todo', 'OAuth Config'),
        ('done', 'Complete')
    ], default='todo', required=True)

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)

        # Get the credentials information
        icp = self.env['ir.config_parameter']
        client_id = icp.get_param('postlogistics.oauth.client_id')
        client_secret = icp.get_param('postlogistics.oauth.client_secret')
        authentication_url = icp.get_param(
            'postlogistics.oauth.authentication_url'
        )
        generate_label_url = icp.get_param(
            'postlogistics.oauth.generate_label_url'
        )
        configuration_done = (
            client_id and
            client_secret and
            authentication_url and
            generate_label_url
        )
        if configuration_done:
            res['client_id'] = client_id
            res['client_secret'] = client_secret
            res['authentication_url'] = authentication_url
            res['generate_label_url'] = generate_label_url
            res['state'] = 'done'

        return res

    @api.multi
    def generate_access_token(self):
        self.ensure_one()

        response = requests.post(
            url=self.authentication_url,
            headers={'content-type': 'application/x-www-form-urlencoded'},
            data={
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'WEDEC_BARCODE_READ',
            },
            timeout=60,
        )

        if response.status_code != 200:
            raise exceptions.UserError(
                _('Access token generation in error\n\n'
                  'Please verify your configuration.'))

        response_dict = json.loads(response.content.decode("utf-8"))
        access_token = response_dict['access_token']

        if not access_token:
            raise exceptions.UserError(
                _('Access token generation in error\n\n'
                  'Please verify your configuration.'))

        # Save the credentials information
        icp = self.env['ir.config_parameter']
        icp.set_param('postlogistics.oauth.client_id', self.client_id)
        icp.set_param('postlogistics.oauth.client_secret', self.client_secret)
        icp.set_param(
            'postlogistics.oauth.authentication_url', self.authentication_url
        )
        icp.set_param(
            'postlogistics.oauth.generate_label_url', self.generate_label_url
        )

        # Define configuration as done
        self.state = 'done'

        # Display configuration
        act = self.env['ir.actions.act_window'].for_xml_id(
            'delivery_carrier_label_postlogistics', 'action_postlogistics_auth'
        )
        act['res_id'] = self.id
        return act

    @api.multi
    def reset_access_token(self):
        # Reset the credentials information
        icp = self.env['ir.config_parameter']
        icp.set_param('postlogistics.oauth.client_id', False)
        icp.set_param('postlogistics.oauth.client_secret', False)
        icp.set_param('postlogistics.oauth.authentication_url', False)
        icp.set_param('postlogistics.oauth.generate_label_url', False)

        # Define configuration as to do
        default_values = self.default_get(
            ['authentication_url', 'generate_label_url', 'state']
        )
        self.client_id = False
        self.client_secret = False
        self.authentication_url = default_values['authentication_url']
        self.generate_label_url = default_values['generate_label_url']
        self.state = default_values['state']

        # Display configuration
        act = self.env['ir.actions.act_window'].for_xml_id(
            'delivery_carrier_label_postlogistics', 'action_postlogistics_auth'
        )
        act['res_id'] = self.id
        return act
