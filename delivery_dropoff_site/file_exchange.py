# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#
##############################################################################

from openerp.osv import orm
import base64
from cStringIO import StringIO
import unicodecsv


DROPOFF_SITE = (
    ('dropoff_site', 'Carrier drop-off sites'),
)


class FileDocument(orm.Model):
    _inherit = "file.document"

    def get_file_document_type(self, cr, uid, context=None):
        res = super(FileDocument, self).get_file_document_type(
            cr, uid, context=context)
        res.extend(DROPOFF_SITE)
        return res

    def get_datas_from_csv_file(
            self, cr, uid, file_doc, fields, dialect,
            encoding="utf-8", context=None):
        str_io = StringIO()
        str_io.writelines(base64.b64decode(file_doc.datas))
        str_io.seek(0)
        return unicodecsv.DictReader(
            str_io, fieldnames=fields,
            encoding=encoding, dialect=dialect)

    def import_datas(self, cr, uid, file_doc, context=None):
        """ Implement in your own module """
        pass

    def create(self, cr, uid, vals, context=None):
        if 'file_type' not in vals:
            vals.update({'file_type': DROPOFF_SITE[0][0]})
        return super(FileDocument, self).create(cr, uid, vals, context=context)

    def _run(self, cr, uid, file_doc, context=None):
        super(FileDocument, self)._run(cr, uid, file_doc, context=context)
        if file_doc.file_type == DROPOFF_SITE[0][0] \
                and file_doc.direction == 'input' \
                and file_doc.repository_id:
            self.import_datas(cr, uid, file_doc, context=context)


class AutomaticTask(orm.Model):
    _inherit = 'automatic.task'

    def get_task_type(self, cr, uid, context=None):
        types = super(AutomaticTask, self).get_task_type(
            cr, uid, context=context)
        types.extend(DROPOFF_SITE)
        return types
