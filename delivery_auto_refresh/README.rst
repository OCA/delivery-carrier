.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===========================================
Auto-refresh delivery price in sales orders
===========================================

This module automates the delivery price handling for the following cases:

* If you change any line in your draft sales order (SO), when saving, the
  delivery price will be adjusted without having to click on "→ Set price".
* If specified in the system parameter, the delivery line can be also
  auto-added when creating/saving.
* If you deliver a different quantity than the ordered one, the delivery price
  is adjusted on the linked SO when the picking is transferred.

Configuration
=============

* Activate developer mode.
* Go to *Settings > Technical > Parameters > System Parameters*.
* Locate the setting with key "delivery_auto_refresh.auto_add_delivery_line"
  or create a new one if not exists.
* Put a non Falsy value (1, True...) if you want to add automatically the
  delivery line on save.

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/99/10.0

Known issues / Roadmap
======================

* After confirming the sales order, the price of the delivery line (if exists)
  will be only updated after the picking is transferred, but not when you
  might modify the order lines.
* There can be some duplicate delivery unset/set for assuring that the refresh
  is done on all cases.
* On multiple deliveries, second and successive pickings update the delivery
  price, but you can't invoice the new delivery price.
* This is only working from user interface, as there's no way of making
  compatible the auto-refresh intercepting create/write methods from sale order
  lines.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/delivery-carrier/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Tecnativa <https://www.tecnativa.com>:
  * Pedro M. Baeza <pedro.baeza@tecnativa.com>

Do not contact contributors directly about support or help with technical issues.

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
