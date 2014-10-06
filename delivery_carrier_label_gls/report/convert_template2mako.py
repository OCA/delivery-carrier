#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

        destination +=  '.mako'
        with open(destination, 'w') as write_file:
            write_file.write(content)

if __name__ == '__main__':
    generate_mako('ZEBRA_FR', 'label')
    generate_mako('ZEBRA_UNISHIP', 'label_uniship')
