# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging
from io import BytesIO

_logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    _logger.debug('Cannot import "PyPDF2". Please make sure it is installed.')


def assemble_pdf(pdf_list):
    """
    Assemble a list of pdf
    """
    output = PdfWriter()
    for pdf in pdf_list:
        if not pdf:
            continue
        reader = PdfReader(BytesIO(pdf))
        for page in reader.pages:
            output.add_page(page)
    s = BytesIO()
    output.write(s)
    return s.getvalue()
