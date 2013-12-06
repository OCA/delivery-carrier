# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
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
from StringIO import StringIO
from PyPDF2 import PdfFileReader, PdfFileWriter

from openerp.osv import orm, fields
from tools.translate import _


def assemble_pdf(pdf_list):
    """
    Assemble a list of pdf
    """
    # Even though we are using PyPDF2 we can't use PdfFileMerger
    # as this issue still exists in mostly used wkhtmltohpdf reports version
    # http://code.google.com/p/wkhtmltopdf/issues/detail?id=635
    #merger = PdfFileMerger()
    #merger.append(fileobj=StringIO(invoice_pdf))
    #merger.append(fileobj=StringIO(bvr_pdf))

    #with tempfile.TemporaryFile() as merged_pdf:
        #merger.write(merged_pdf)
        #return merged_pdf.read(), 'pdf'

    output = PdfFileWriter()
    for pdf in pdf_list:
        reader = PdfFileReader(StringIO(pdf))
        for page in range(reader.getNumPages()):
            output.addPage(reader.getPage(page))
    s = StringIO()
    output.write(s)
    return s.getvalue()


class DeliveryCarrierLabelGenerate(orm.TransientModel):

    _name = 'delivery.carrier.label.generate'

    def _get_dispatch_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = False
        if (context.get('active_model') == 'picking.dispatch'
                and context.get('active_ids')):
            res = context['active_ids']
        return res

    _columns = {
        'dispatch_ids': fields.many2many('picking.dispatch',
                                         string='Picking Dispatch'),
        'label_pdf_file': fields.binary('Labels file'),
    }

    _defaults = {
        'dispatch_ids': _get_dispatch_ids,
    }

    def action_generate_labels(self, cr, uid, ids, context=None):
        """
        Call the creation of the delivery carrier label
        of the missing labels and get the existing ones
        Then merge all of them in a single PDF
        """
        context = context or {}
        this = self.browse(cr, uid, ids, context=context)[0]
        if not this.dispatch_ids:
            raise orm.except_orm(_('Error'), _('No picking dispatch selected'))

        picking_out_obj = self.pool.get('stock.picking.out')

        # flatten all ids
        picking_ids = [picking.id for dispatch in this.dispatch_ids
                       for picking in dispatch.related_picking_ids
                       if not picking.get_pdf_label()[picking.id]]
        # generate missing picking labels
        picking_out_obj.action_generate_carrier_label(cr, uid,
                                                      picking_ids,
                                                      #file_type='pdf',
                                                      context=context)

        data_list = [picking.get_pdf_label()[picking.id]
                     for dispatch in this.dispatch_ids
                     for picking in dispatch.related_picking_ids]
        pdf_list = [data.decode('base64') for data in data_list if data]
        pdf_file = assemble_pdf(pdf_list)
        this.write({'label_pdf_file': pdf_file.encode('base64')})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.carrier.label.generate',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
