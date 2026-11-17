# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging

from odoo.tools.pdf import merge_pdf

_logger = logging.getLogger(__name__)


def assemble_pdf(pdf_list):
    """
    Assemble a list of pdf
    """
    valid_pdfs = [pdf for pdf in pdf_list if pdf]
    if not valid_pdfs:
        return b""
    if len(valid_pdfs) == 1:
        return valid_pdfs[0]
    return merge_pdf(valid_pdfs)
