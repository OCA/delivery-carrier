# -*- coding: utf-8 -*-
# Copyright 2018 Halltic eSolutions S.L.
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import imghdr
import logging
import urllib
import urllib2
import os

from odoo import models, api
from odoo import tools

_logger = logging.getLogger(__name__)


class Image(models.Model):
    _inherit = "base_multi_image.image"

    @api.model
    @tools.ormcache("url")
    def _get_image_from_url_cached(self, url):
        """Allow to download an image and cache it by its URL."""
        if url:
            if isinstance(url, unicode):
                url = url.encode('utf8')
            try:
                (filename, header) = urllib.urlretrieve(url)
                if not imghdr.what(filename):
                    raise Exception('This file is not an image (%s)' % filename)
                with open(filename, 'rb') as f:
                    return base64.b64encode(f.read())
            except:
                _logger.error("URL %s cannot be fetched or it isn't an image",
                              url,
                              exc_info=True)
                try:
                    request = urllib2.Request(url=url,
                                              headers={
                                                  'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0'})
                    binary = urllib2.urlopen(request)
                    return base64.b64encode(binary.read())
                except:
                    return False

        return False

    @api.model
    def _get_name_extension_from_url(self, url):
        if url:
            filename = url.split('/')[-1]
            name, extension = os.path.splitext(filename)
            name = self._make_name_pretty(name)
            return name
