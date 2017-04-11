.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================
Delivery Carrier SEUR
=====================

This module was written to extend the functionality of base_delivery_carrier_label module to support shippings with Seur as carrier and allow you to generate the corresponding labels, manifest, etc.

Installation
============

This module use the Seur API: https://pypi.python.org/pypi/seur

Configuration
=============

To configure this module, you need to:

* Set the **carrier config**:

 * Go to *Settings/Configuration/Carriers*
 * Create new record:

  * Seur have to provide the integration, accounting and franchise codes and username/password
  * The format expected for **VAT** field is AXXXXXXXX and not ESAXXXXXXX
  * The **file type** is 'txt' if you use a Zebra printer

* Set the **delivery method**:

 * Go to *Warehouse/Configuratio/Delivery Methods*
 * Create new record:

  * Set SEUR as *type*
  * In the *SEUR Config*, set the config created previously
  * The *Service and Product Codes* will be the default options but you will be able to choose others in the stock picking. You have some info about Seur services and products here: http://www.seur.com/contenido/oferta-general/transporte-nacional/urgencia.html
  * For *Transport Company* just create a partner for Seur
  * For *Delivery Product* select or create a product for shipping costs

Usage
=====

You have to set Seur carrier in the stock picking you want to ship:
 * In the stock picking form go to *Additional Info* tab and choose Seur as carrier and the service and product code. You only be able to choose this if the state of the picking is 'Ready to Transfer.
 * When the picking is 'Transferred', it appears a *Create Shipping Label* button. Just push it, and if all went well the label will be 'attached'

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/99/8.0

Known issues / Roadmap
======================

This module allows to:
 * Generate label and tracking number
 * Generate manifesto

TODO
----

 * Cash on delivery
 * Edit/delete delivery tracking
 * Customs management
 * ...

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/
carrier-delivery/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback `here <https://github.com/OCA/
carrier-delivery/issues/new?body=module:%20
delivery_carrier_seur%0Aversion:%20
8.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Ismael Calvo <ismael.calvo@factorlibre.com>
* Angel Moya <angel.moya@pesol.es>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
