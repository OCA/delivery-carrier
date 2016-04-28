# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#
##############################################################################

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    laposte_login = fields.Char(
        string='Login',
        size=6,
        help=u"Nombre à 6 caractères.\n"
             u"La valeur par défaut est 964744")
    laposte_password = fields.Char(
        string='mot de passe site web',
        help=u"le mot de passe est celui de votre espace client.\n")
    laposte_support_city = fields.Char(
        string='Site de Prise en Charge',
        size=64,
        help="Nom du site de prise en charge de la poste pour son client.\n"
             "Indiquer votre centre de rattachement")
    laposte_support_city_code = fields.Char(
        string='Code Site de Prise en Charge',
        size=6,
        help="Code du site de prise en charge")
    laposte_unittest_helper = fields.Boolean(
        'Unit Test Helper',
        help=u"Seulement utile pour les développeurs.\n"
             u"Si coché enregistre les données du picking ColiPoste\n"
             u"dans le dossier temporaire système du serveur.\n"
             u"Ce fichier peut être utilisé pour créer "
             u"de nouveaux tests unitaires python")
    laposte_webservice_message = fields.Boolean(
        u'Enregistre les Messages du Webservice',
        help=u"Pour ColiPoste International. \nSi coché, un commentaire "
             u"sera créé dans le bon de livraison\nsi la réponse du "
             u"web service contient un message additionnel.")

