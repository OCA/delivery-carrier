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
import os
import logging
from suds.client import Client
from suds.plugin import MessagePlugin

_logger = logging.getLogger(__name__)


class LogPlugin(MessagePlugin):
    def sending(self, context):
        _logger.info(context.envelope.decode('utf-8', errors='ignore'))

    def received(self, context):
        _logger.info(context.reply.decode('utf-8', errors='ignore'))


class DelnextBase(object):

    def __init__(self, delnext_config):
        self.delnext_config = delnext_config


class DelnextEnvio(DelnextBase):

    def __init__(self, delnext_config):
        self.delnext_config = delnext_config
        super(DelnextEnvio, self).__init__(self.delnext_config)
