# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 Halltic eSolutions S.L. (http://www.halltic.com)
#                  Tristán Mozos <tristan.mozos@halltic.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import json
import os
import logging

import requests
from suds.plugin import MessagePlugin

_logger = logging.getLogger(__name__)


class LogPlugin(MessagePlugin):
    def sending(self, context):
        _logger.info(context.envelope.decode('utf-8', errors='ignore'))

    def received(self, context):
        _logger.info(context.reply.decode('utf-8', errors='ignore'))


class SpringBase(object):

    def __init__(self, spring_config):
        self._spring_config = spring_config
        if self._spring_config.is_test:
            self._url = 'https://mtapi.net/?testMode=1'
        else:
            self._url = 'https://mtapi.net/'


class SpringRequest(SpringBase):

    def api_request(self, data):
        headers = {'Content-type':'text/json', 'Accept':'text/plain'}
        data['Apikey'] = self._spring_config.api_key
        r = requests.post(self._url, data=json.dumps(data), headers=headers)
        if r.status_code == 200:
            return json.loads(r.text)
