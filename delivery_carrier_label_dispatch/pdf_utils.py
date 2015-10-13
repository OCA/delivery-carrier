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


def assemble_pdf(pdf_list):
    """
    Assemble a list of pdf
    """
    # Even though we are using PyPDF2 we can't use PdfFileMerger
    # as this issue still exists in mostly used wkhtmltohpdf reports version
    # http://code.google.com/p/wkhtmltopdf/issues/detail?id=635
    # merger = PdfFileMerger()
    # merger.append(fileobj=StringIO(invoice_pdf))
    # merger.append(fileobj=StringIO(bvr_pdf))

    # with tempfile.TemporaryFile() as merged_pdf:
    #     merger.write(merged_pdf)
    #     return merged_pdf.read(), 'pdf'

    output = PdfFileWriter()
    for pdf in pdf_list:
        if not pdf:
            continue
        reader = PdfFileReader(StringIO(pdf))

        for page in range(reader.getNumPages()):
            output.addPage(reader.getPage(page))
    s = StringIO()
    output.write(s)
    return s.getvalue()
