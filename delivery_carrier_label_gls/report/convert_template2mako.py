# coding: utf-8
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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
