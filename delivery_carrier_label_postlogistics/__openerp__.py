# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
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
##############################################################################
{'name': 'PostLogistics Labels WebService',
 'version': '1.0',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'version',
 'complexity': 'normal',
 'depends': ['base_delivery_carrier_label'],
 'description': """
PostLogistics Labels WebService
===============================

Description
-----------

This module uses `PostLogistics BarCodes WebService`_ to generate labels
for your Delivery Orders.

It adds a `Create label` button on Delivery Orders.
A generated label will be an attachement of your Delivery Order.

To see it, please install documents module.

You can create multiple delivery method to match your diffent package types.


Configuration
-------------

.. important::
   A "Swiss Post Business customer" account is required to use this module.

   See `Swiss Post E-logistics`_


To configure:

* Go to `Configurations -> Settings -> Postlogistics`
* Set your login informations
* launch the Update PostLogistics Services

This will load available services and generate carrier options.

Now you can create a carrier method for PostLogistics WebService:

* First choose a Service group and save
* Add a Mandatory Carrier option using a Basic Service
* Save Carrier Method (this will update filters to show you only
  compatible services)
* Then add other `Optional as default` and `Optional` carrier option
  from listed
* Additional Service and Delivery instructions

.. _PostLogistics BarCodes WebService: http://www.poste.ch/post-startseite/post-geschaeftskunden/post-logistik/post-e-log/post-e-log-webservices.htm
.. _Swiss Post E-logistics: http://www.poste.ch/en/post-startseite/post-geschaeftskunden/post-logistik/post-e-log.htm

Technical references
--------------------

`"Barcode" web service documentation`_

.. _"Barcode" web service documentation: http://www.poste.ch/post-barcode-cug.htm

Contributors
------------

* Yannick Vaucher <yannick.vaucher@camptocamp.com>

----

*TODO*:

* *Add onchange to improve carrier method creation*
* *Default options*
* *Identify attachement as label*
* *Better License management*
""",
 'website': 'http://www.camptocamp.com/',
 'data': ['res_partner_data.xml',
          'delivery_data.xml',
          'delivery_view.xml',
          'res_config_view.xml',
          ],
 'tests': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': True,
 'external_dependencies': {
    'python': ['suds'],
 }
 }
