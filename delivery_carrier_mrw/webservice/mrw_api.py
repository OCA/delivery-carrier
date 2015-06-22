##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 FactorLibre (http://www.factorlibre.com)
#                  Hugo Santos <hugo.santos@factorlibre.com>
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

_logger = logging.getLogger(__name__)


class MrwBase(object):

    def __init__(self, mrw_config, wsdl_name):
        wsdl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'wsdl')
        self.mrw_config = mrw_config
        if self.mrw_config.is_test:
            self.wsdl_path = os.path.join(wsdl_path, 'wsdl_test', wsdl_name)
        else:
            self.wsdl_path = os.path.join(wsdl_path, wsdl_name)

        self.client = Client('file:///%s' % self.wsdl_path.lstrip('/'))


class MrwEnvio(MrwBase):

    def __init__(self, mrw_config):
        self.mrw_config = mrw_config
        super(MrwEnvio, self).__init__(self.mrw_config, 'MRWEnvio.wsdl')

        auth_info = self.client.factory.create('AuthInfo')
        auth_info.CodigoFranquicia = self.mrw_config.franchise_code
        auth_info.CodigoAbonado = self.mrw_config.subscriber_code
        auth_info.CodigoDepartamento = self.mrw_config.department_code
        auth_info.Username = self.mrw_config.username
        auth_info.Password = self.mrw_config.password

        self.client.set_options(soapheaders=auth_info)