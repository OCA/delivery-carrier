.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================================================
Multiple destinations for the same delivery method
==================================================

Module `delivery` in version 8 allows to set different price rules depending
on the destination. This is what is called a delivery grid.

In version 9, for simplifying delivery methods, Odoo has plained the structure,
lowering destinations at delivery method level, and removing delivery grid
model.

This is not usable when you have different prices according the destination
of your delivery.

This module restores the same concept, reusing the same model for nesting
several "children" delivery methods, one per possible destination. It has been
designed to reuse all possible extensions to the base delivery, without the
need to create a glue module for having multiple destinations.

This module also handles if you're migrating from version 8 and you had
`delivery` module installed, to keep the delivery grids.

Installation
============

If you installed the module on a version 8 migrated database, some operations
will be done for recovering delivery grids. If so, you need to have
**openupgradelib** library installed.

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
   :target: https://runbot.odoo-community.org/runbot/99/9.0

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
