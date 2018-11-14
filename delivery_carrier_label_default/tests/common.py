# Copyright 2017-2018 Simone Orsi
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""Mixin copied and adapted from
https://github.com/OCA/website-cms/blob/11.0/cms_form/tests/common.py
"""
from lxml import html


class HTMLRenderMixin(object):
    """Mixin with helpers to test HTML rendering."""

    def to_xml_node(self, html_):
        return html.fragments_fromstring(html_)

    def find_div_class(self, node, name):
        return node.xpath(
            '(//div)[@class="{}"]'.format(name))
