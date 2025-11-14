Delivery Carrier Geodis
=======================


Description
-----------
Send parcels with Geodis.
Labels are generated from WebServices.
Edi file is generated locally and should be sent
by another module.

Glossary
--------

Agency: Geodis's hub your warehouse depends upon.

Configuration

## Create a partner for your agency.

This modules comes with only one partner "Geodis". It's the head quarters of Geodis.
You need to create partners for the agency you depends : 
- create a sub contact of "Geodis HQ",
- pay attention to fill correctly name, streets, phone, zip code, country and *SIRET*
- fill "ref" (internal reference) field with the agency id.


Features:
- Multiple Agencies. 

Known Issues:
~~~~~~~~~~~~~

- each pack is sent on his own : no handling of numbers of picking


Technical references
--------------------

'Geodis documentation: www.geodis.fr'

Contributors
------------

* Raphaël REVERDY <raphael.reverdy@akretion.com>
* Eric Bouhana <monsieurb@saaslys.com>

