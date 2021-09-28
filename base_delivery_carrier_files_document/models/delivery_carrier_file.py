# -*- coding: utf-8 -*-
# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from openerp import api, models


class DeliveryCarrierFile(models.Model):
    _inherit = 'delivery.carrier.file'

    @api.model
    def get_write_mode_selection(self):
        res = super(DeliveryCarrierFile, self).get_write_mode_selection()
        if 'document' not in [a[0] for a in res]:
            res.append(('document', 'Document'))
        return res

    @api.model
    def _prepare_attachment(self, carrier_file, filename, file_content):
        return {'name': "%s_%s" % (carrier_file.name, filename),
                'datas_fname': filename,
                'datas': base64.encodestring(file_content),
                'type': 'binary'}

    @api.multi
    def _write_file(self, filename, file_content):
        ret = True
        for this in self:
            if this.write_mode == 'document':
                vals = self._prepare_attachment(
                    this, filename, file_content)
                self.env['ir.attachment'].create(vals)
                ret &= True
            else:
                ret &= super(DeliveryCarrierFile, this)._write_file(
                    filename, file_content)
        return ret
