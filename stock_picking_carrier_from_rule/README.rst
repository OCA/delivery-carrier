===============================
Stock Picking Carrier From Rule
===============================

.. 
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! This file is generated by oca-gen-addon-readme !!
   !! changes will be overwritten.                   !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! source digest: sha256:2c1743619bfa5b2c748924afb1cff410d90106059ccb9f5bcfcf1dba32dd6fec
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fdelivery--carrier-lightgray.png?logo=github
    :target: https://github.com/OCA/delivery-carrier/tree/14.0/stock_picking_carrier_from_rule
    :alt: OCA/delivery-carrier
.. |badge4| image:: https://img.shields.io/badge/weblate-Translate%20me-F47D42.png
    :target: https://translation.odoo-community.org/projects/delivery-carrier-14-0/delivery-carrier-14-0-stock_picking_carrier_from_rule
    :alt: Translate me on Weblate
.. |badge5| image:: https://img.shields.io/badge/runboat-Try%20me-875A7B.png
    :target: https://runboat.odoo-community.org/builds?repo=OCA/delivery-carrier&target_branch=14.0
    :alt: Try me on Runboat

|badge1| |badge2| |badge3| |badge4| |badge5|

This module sets a shipping method on stock picking based on the partner address
set on the stock rule.
If the value for `carrier_id` is not yet set on the picking. And the partner as
a delivery method set.

**Table of contents**

.. contents::
   :local:

Known issues / Roadmap
======================

Add unit tests

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/delivery-carrier/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
`feedback <https://github.com/OCA/delivery-carrier/issues/new?body=module:%20stock_picking_carrier_from_rule%0Aversion:%2014.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Camptocamp

Contributors
~~~~~~~~~~~~

* Thierry Ducrest <thierry.ducrest@camptocamp.com>
* `Trobz <https://trobz.com>`_:
    * Khoi Vo <khoivha@trobz.com>

Other credits
~~~~~~~~~~~~~

The migration of this module from 13.0 to 14.0 was financially supported by Camptocamp

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/delivery-carrier <https://github.com/OCA/delivery-carrier/tree/14.0/stock_picking_carrier_from_rule>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
