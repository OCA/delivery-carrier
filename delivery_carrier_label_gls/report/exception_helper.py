# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2014-TODAY Akretion <http://www.akretion.com>.
#     All Rights Reserved
#     @author David BEAL <david.beal@akretion.com>
#             Sébastien BEAU <sebastien.beau@akretion.com>
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


class InvalidAccountNumber(Exception):
    pass


class InvalidSequence(Exception):
    pass


class InvalidWeight(Exception):
    pass


class InvalidSize(Exception):
    pass


class InvalidType(Exception):
    pass


class InvalidValue(Exception):
    pass


class InvalidValueNotInList(Exception):
    pass


class InvalidMissingField(Exception):
    pass


class InvalidZipCode(Exception):
    pass


class InvalidCountry(Exception):
    pass


class InvalidDate(Exception):
    pass


class InvalidCode(Exception):
    pass


class InvalidKeyInTemplate(Exception):
    pass
