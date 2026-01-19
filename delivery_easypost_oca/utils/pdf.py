# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging
from io import BytesIO

_logger = logging.getLogger(__name__)

try:
    try:
        from PyPDF2 import PdfReader, PdfWriter  # pylint: disable=W0404
    except ImportError:
        from PyPDF2 import (  # pylint: disable=W0404
            PdfFileReader as PdfReader,
        )
        from PyPDF2 import (
            PdfFileWriter as PdfWriter,
        )
except ImportError:
    _logger.debug("Can not import PyPDF2")


def assemble_pdf(pdf_list):
    """
    Assemble a list of pdf
    """
    output = PdfWriter()
    for pdf in pdf_list:
        if not pdf:
            continue
        reader = PdfReader(BytesIO(pdf))

        # Handle both PyPDF2 < 3.0 and >= 3.0 API differences
        if hasattr(reader, "pages"):
            # PyPDF2 >= 3.0
            pages = reader.pages
        else:
            # PyPDF2 < 3.0
            pages = [reader.getPage(i) for i in range(reader.getNumPages())]

        for page in pages:
            # Handle both PyPDF2 < 3.0 (addPage) and >= 3.0 (add_page)
            if hasattr(output, "add_page"):
                output.add_page(page)
            else:
                output.addPage(page)
    s = BytesIO()
    output.write(s)
    return s.getvalue()
