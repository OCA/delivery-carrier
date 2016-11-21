.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

================================
Delivery Carrier Label GLS Group
================================


GLS Group - Transportation services
+++++++++++++++++++++++++++++++++++

Unibox service implementation:

- send delivery order informations and parcel info to the GLS unibox server
- webservice routing info in background
- label GLS Unibox generation


GLS carrier https://gls-group.eu/

|

Configuration
=============

To configure this module, you need to:

# Go to the menu Settings > Configuration > Warehouse, and check 'Use packages: pallets, boxes'
# Go to the menu Settings > Configuration > Carriers > GLS
# Complete account parameters
# Complete company country in Settings > Companies

.. image:: /delivery_carrier_label_gls/static/description/gls1.png
   :alt: Account GLS settings by company Odoo ERP

|

Usage
=====

To use this module, you need to create a Delivery Order with Carrier field 'GLS Group'

Odoo Delivery Order with GLS carrier
++++++++++++++++++++++++++++++++++++

.. image:: delivery_carrier_label_gls/static/description/gls2.png
   :alt: Odoo Delivery Order avec GLS carrier with Odoo ERP
   :width: 900 px

|

GLS transport label towards France generated with Odoo ERP
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. image:: /delivery_carrier_label_gls/static/description/gls3.png
   :alt: GLS transport label towards France generated with Odoo ERP

|

GLS transport label towards foreign countries
+++++++++++++++++++++++++++++++++++++++++++++

.. image:: /delivery_carrier_label_gls/static/description/gls4.png
   :alt: GLS transport label towards foreign countries

|

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/99/8.0

|


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/carrier-delivery/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/OCA/
carrier-delivery/issues/new?body=module:%20
delivery_carrier_label_gls%0Aversion:%20
8.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* David BEAL <david.beal@akretion.com>

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
