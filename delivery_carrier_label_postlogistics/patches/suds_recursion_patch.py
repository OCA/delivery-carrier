# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from logging import getLogger

from odoo.exceptions import UserError
from odoo import _

_logger = getLogger(__name__)

try:
    from suds.xsd.schema import Schema
    from suds.transport import TransportError
    from suds.reader import DocumentReader
except ImportError:
    _logger.warning(
        'suds library not found. '
        'If you plan to use it, please install the suds library '
        'from https://pypi.python.org/pypi/suds')


PROCESSED_IMPORTS_CACHE = {}
PROCESSED_IMPORT_DEPTH = {}
MAX_IMPORT_DEPTH = 3


def _patched_instance(self, root, baseurl, options):
    """
    Dynamic implementation of
    delivery_carrier_label_postlogistics/patches/suds_recursion.patch
    (https://fedorahosted.org/suds/attachment/ticket/239/suds_recursion.patch)
    so it's done automatically when the module is loaded.

    Create and return an new schema object using the
    specified I{root} and I{url}.
    @param root: A schema root node.
    @type root: L{sax.element.Element}
    @param baseurl: A base URL.
    @type baseurl: str
    @param options: An options dictionary.
    @type options: L{options.Options}
    @return: The newly created schema object.
    @rtype: L{Schema}
    @note: This is only used by Import children.
    """
    global PROCESSED_IMPORTS_CACHE, PROCESSED_IMPORT_DEPTH, MAX_IMPORT_DEPTH
    if baseurl not in PROCESSED_IMPORTS_CACHE:
        if baseurl in PROCESSED_IMPORT_DEPTH:
            if (PROCESSED_IMPORT_DEPTH[baseurl] < MAX_IMPORT_DEPTH):
                PROCESSED_IMPORT_DEPTH[baseurl] += 1
                _logger.debug('Increasing import count for: %s' % baseurl)
            else:
                _logger.debug(
                    'Maxdepth (%d) reached; Skipping processed import: %s' % (
                        MAX_IMPORT_DEPTH, baseurl))
                return None
        else:
            PROCESSED_IMPORT_DEPTH[baseurl] = 1
            _logger.debug('Importing for the first time: %s' % baseurl)

        PROCESSED_IMPORTS_CACHE[baseurl] = Schema(root, baseurl, options)
        _logger.debug('Successfully cached import: %s' % baseurl)
    else:
        _logger.debug('Retrieving import from cache: %s' % baseurl)
    return PROCESSED_IMPORTS_CACHE[baseurl]


def _patched_open(self, url):
    """
    Patch of suds.reader.DocumentReader.open to restore the error message
    which is discarded on suds.xsd.sxbasic.Import.download
    (https://bitbucket.org/jurko/suds/src/0fcfff1ea149397bfa23c7537a0ae2ac300e9564/suds/xsd/sxbasic.py?at=release-0.6&fileviewer=file-view-default#sxbasic.py-602)  # noqa
    """
    try:
        return self.orig_open(url)
    except TransportError as e:
        msg = _('%s : Connection error to retrieve URL : %s') % (str(e), url)
        _logger.error(msg, exc_info=True)
        if e.httpcode == 401:
            raise UserError(_('%s. Please check your credentials.') % msg)
        raise Exception(msg)


def patch_suds():
    """Apply patches to suds library."""
    Schema.orig_instance = Schema.instance
    Schema.instance = _patched_instance
    DocumentReader.orig_open = DocumentReader.open
    DocumentReader.open = _patched_open
    _logger.info('Suds library patched successfully !')
