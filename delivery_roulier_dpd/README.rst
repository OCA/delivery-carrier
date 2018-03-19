====================
Delivery Roulier DPD
====================

Send and track parcels with DPD France.

Products available: 'Classic', 'Predict', and 'Relais'.
(previously known as Ici Relais and Exapaq).

Installation
============

To install this module, you need to:

- Install `Roulier <https://pypi.python.org/pypi/roulier>`_ library like ::

  $ pip install roulier
- Install `Cerberus <http://docs.python-cerberus.org/en/stable/>`_ ::

  $ pip install cerberus

Configuration
=============

Go to Settings > Keychain to configure your account.
Note: if it's your first account with keychain, you have to generate a key.
See `keychain's documentation <https://github.com/OCA/server-tools/tree/9.0/keychain>`_.

Make sure your users have the "Manage Packages" rights.

Usage
=====

From a draft outgoing picking, choose one of the DPD delivery methods.
After the transfert, click on "Generate Shipping Label" button.
The labels are attached on the picking.


Known issues / Roadmap
======================

- Only DPD France is supported.
- Packages are sent one by one (no grouping by pickings)
- Returns are not supported
- Configuration through keychain can be more user friendly with 'keychain backends'.

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

* Raphaël REVERDY <raphael.reverdy@akretion.com> https://akretion.com
* Eric Bouhana <monsieurb@saaslys.com>

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
