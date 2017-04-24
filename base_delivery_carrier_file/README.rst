.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============================
Base module for carrier files
=============================

Base module for creation of carrier files (La Poste, TNT Express Shipper, ...).
Files are exported as text (csv, ...).
It contains :
- the base structure to handle the export of files on Delivery Orders
- an API to ease the generation of the files for the developers in sub-modules.

The delivery orders can be grouped in one files
or be exported each one in a separate file.
The files can be generated automatically
on the shipment of a Delivery Order or from a manual action.
They are exported to a defined path or
in a document directory of your choice if the "document" module is installed.

A generic carrier file is included in the module.
It can also be used as a basis to create your own sub-module.

Sub-modules already exist to generate file according to specs of :
 - La Poste (France) : delivery_carrier_file_laposte
 - TNT Express Shipper (France) : delivery_carrier_file_tnt
 - Make your own ! Look at the code of the modules above,
   it's trivial to create a sub-module for a carrier.

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/99/9.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/
carrier-delivery/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Guewen Baconnier Camp2Camp
* Angel Moya <angel.moya@pesol.es>


Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
