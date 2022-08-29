# Copyright 2012 Camptocamp SA
# Copyright 2021 Sunflower IT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import api, models


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
        file_c = file_content.encode("utf-8")
        return {
            'name': "%s_%s" % (carrier_file.name, filename),
            'datas': base64.b64encode(file_c),
            'type': 'binary'
        }

    def _write_file(self, filename, file_content, pickings):
        ret = True
        for this in self:
            if this.write_mode == 'document':
                vals = self._prepare_attachment(
                    this, filename, file_content)
                self.env['ir.attachment'].create(vals)
                ret &= True
            else:
                ret &= super(DeliveryCarrierFile, this)._write_file(
                    filename, file_content, pickings)
        return ret
