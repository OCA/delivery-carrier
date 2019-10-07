.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==================================================
Multiple destinations for the same delivery method
==================================================

This module allows to set different price rules depending on the destination.

This module restores the concept of delivery grid, reusing the same model for
nesting several "children" delivery methods, one per possible destination.
It has been designed to reuse all possible extensions to the base delivery,
without the need to create a glue module for having multiple destinations.

Configuration
=============

To configure delivery methods with multiple destinations:

#. Go to Inventory > Configuration > Delivery > Delivery Methods
#. Create or edit an existing record.
#. Select "Destination type" = "Multiple destinations".
#. Introduce a line for each destination in the new tab "Destinations"
#. Lines have priority, so you have to put first the lines with more restricted
   destinations.

Usage
=====

#. When using the delivery method in a Sales order, delivery address will be
   used for computing the delivery price according introduced destinations.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/99/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/delivery-carrier/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Luis M. Ontalba <luis.martinez@tecnativa.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
