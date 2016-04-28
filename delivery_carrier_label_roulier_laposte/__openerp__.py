# -*- coding: utf-8 -*-

{
    'name': 'LaPoste',
    'version': '0.3',
    'author': 'Akretion',
    'summary': 'Ship with Coliposte, Colissimo, So-colissimo and so on',
    'maintainer': 'Akretion',
    'category': 'Warehouse',
    'depends': [
        'delivery_carrier_b2c',
        'delivery_carrier_label_roulier',
    ],
    'description': """
Delivery Carrier ColiPoste
==========================


Description
-----------

Company:
~~~~~~~~~~
Some informations have to be filled on two locations :

* company form (Settings > Companies > Companies):
complete address of the company, included phone

* config<uration form (Settings > Configuration > Carriers > ColiPoste) :
the default test account number is 964744



Technical references
--------------------

`ColiPoste documentation`_

.. _documentation: https://www.coliposte.net

Contributors
------------

* David BEAL <david.beal@akretion.com>
* Benoit GUILLOT <benoit.guillot@akretion.com> (EDI part)
* Sébastien BEAU <sebastien.beau@akretion.com>
* Raphaël REVERDY <raphael.reverdy@akretion.com>

----

    """,
    'website': 'http://www.akretion.com/',
    'data': [
        'data/delivery.xml',
        'config_view.xml',
        'stock_view.xml',
    ],
    'demo': [
        #   'demo/res.partner.csv',
        #   'demo/company.xml',
        #   'demo/product.xml',
    ],
    'tests': [],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
