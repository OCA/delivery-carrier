.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============================
PostLogistics Labels WebService
===============================

This module uses `PostLogistics BarCodes WebService`_ to generate labels
for your Delivery Orders.

It adds a `Create label` button on Delivery Orders.
A generated label will be an attachement of your Delivery Order.

To see it, please install documents module.

You can create multiple delivery method to match your diffent package types.

Installation
------------

As a requirement you need to install `suds-jurko` library. It will fail with the
latest and outdated version of `suds`.
https://pypi.python.org/pypi/suds-jurko/0.6


Furthermore, if you want to use the integration server of Postlogistics
you will have to patch this library with the following patch:

https://fedorahosted.org/suds/attachment/ticket/239/suds_recursion.patch

A copy of this patch is available in `patches` folder of this module.


Configuration
-------------

.. important::
   A "Swiss Post Business customer" account is required to use this module.

   See `Log in`_


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
* Add additional Service and Delivery instructions

.. _PostLogistics BarCodes WebService: https://www.post.ch/en/business/a-z-of-subjects/dropping-off-mail-items/business-sending-letters/sending-consignments-web-service-barcode
.. _Log in: https://account.post.ch/selfadmin/?login&lang=en


Technical references
--------------------

`"Barcode" web service documentation`_

.. _"Barcode" web service documentation: https://www.post.ch/en/business/a-z-of-subjects/dropping-off-mail-items/business-sending-letters/barcode-support


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/carrier-delivery/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.
