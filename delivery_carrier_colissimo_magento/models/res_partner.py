# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper
                                                  )
from openerp.addons.magentoerpconnect.backend import magento


@magento
class PartnerImportMapper(ImportMapper):
    _model_name = 'magento.res.partner'

    @mapping
    def names(self, record):
        res = super(PartnerImportMapper, self).names(record)
        res.update({'external_firstname': record['firstname'],
                    'external_middlename': record['middlename'],
                    'external_lastname': record['lastname'],
                    })
        return res
