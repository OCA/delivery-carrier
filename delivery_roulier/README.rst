================
Delivery Roulier
================

This module provide base integration for carriers trough the library "roulier".
You should install carrier specific modules like delivery_roulier_laposte or delivery_roulier_dpd.

Installation
============

To install this module, you need to:

#. Install `Roulier <https://pypi.python.org/pypi/roulier>`_ library like ::

   $ pip install roulier


Configuration
=============

This module makes use of packages.
Make sure your users have "Manage Packages" rights. (With 'debug mode' activated, edit 'Users' from 'Settings' menu.)


Usage
=====

To use this module, you need to install carrier specific modules.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/github-com-oca-carrier-delivery-99


Known issues / Roadmap
======================

* Write tests
* Harmonize decorators (done in v10)

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/delivery-carrier/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Raphael Reverdy <raphael.reverdy@akretion.com> https://akretion.com
* David BEAL <david.beal@akretion.com> https://akretion.com

Do not contact contributors directly about support or help with technical issues.

Funders
-------

The development of this module has been financially supported by:

* Akretion


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
