.. important::
   A "Swiss Post Business customer" account is required to use this module.

   See `Log in`_


To configure:

* Go to `Inventory -> Configuration -> Delivery -> Shipping Methods`
* Create new shipping methods for postlogistics and set your login informations
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

.. _Log in: https://account.post.ch/selfadmin/?login&lang=en

Technical references
~~~~~~~~~~~~~~~~~~~~

`"Barcode" web service documentation`_

.. _"Barcode" web service documentation: https://www.post.ch/en/business/a-z-of-subjects/dropping-off-mail-items/business-sending-letters/barcode-support
