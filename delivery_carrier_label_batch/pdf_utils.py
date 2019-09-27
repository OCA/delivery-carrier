# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from io import BytesIO
import logging

_logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileReader, PdfFileWriter
except ImportError:
    _logger.debug('Cannot import "PyPDF2". Please make sure it is installed.')


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
        reader = PdfFileReader(BytesIO(pdf))

        for page in range(reader.getNumPages()):
            output.addPage(reader.getPage(page))
    s = BytesIO()
    output.write(s)
    return s.getvalue()
