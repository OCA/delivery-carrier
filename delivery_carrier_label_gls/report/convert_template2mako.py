# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) All Rights Reserved 2014 Akretion
#    @author David BEAL <david.beal@akretion.com>
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
###############################################################################

"""
This file is only used to convert epl/zpl files provided by GLS
in valid mako template file
"""


def generate_mako(source, destination):
    with open(source + '.txt', 'r') as content_file:
        content = content_file.read()

        content = '## -*- coding: utf-8 -*-\n' + content
        content = content.replace('<', '${')
        content = content.replace('>', '}')
        # standard label
        content = content.replace('^FO675,203^AB,8,10^FDPRODUIT^FS', '')
        content = content.replace('^FO500,222^AB,12,15^FD${T8912}^FS', '')
        content = content.replace(
            '^FO520,222^AB,12,15^', '^FO500,222^AB,12,15^')
        content = content.replace(
            '^FO55,620^B2', '\n/* Barcode */\n^FO55,620^B2')
        # uniship label
        content = content.replace('^FO480,530^A0,30,20', '^FO480,560^A0,30,20')
        content = content.replace('^FO90,500^BX', '^FO90,470^BX')

        destination += '.mako'
        with open(destination, 'w') as write_file:
            write_file.write(content)


if __name__ == '__main__':
    generate_mako('ZEBRA_FR', 'label')
    generate_mako('ZEBRA_UNISHIP', 'label_uniship')
