.. image:: https://img.shields.io/badge/license-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==============
Stock Delivery
==============

This module provides extended stock functionality associated with deliveries, such as:

* Multiple carrier deliveries for a stock picking
* Delivery packaging types & dimensions
* Concept of multiple delivery rate quotes for a delivery
* Concept of shipping labels
* Concept of tracking stages & locations

While this module does provide the concepts and wizards, it is not really that useful
without an external connector module such as ``connector-easypost``.

Installation
============

Configuration
=============

* Enable package tracking in Warehouse settings

Usage
=====

Most of this module revolves around data models, however a few actions do exist

Delivery Wizard
---------------

The Delivery Wizard is accessed when `Put In Pack` is utilized in a stock picking.

Creates a Stock Quant Package & associates to Delivery Group + Delivery Package.

This would be the first stage in triggering a shipment, and subsequent label quote if utilizing
an external system.


Credits
=======

Images
------

* LasLabs: `Icon <https://repo.laslabs.com/projects/TEM/repos/odoo-module_template/browse/module_name/static/description/icon.svg?raw>`_.

Contributors
------------

* Dave Lasley <dave@laslabs.com>

Maintainer
----------

.. image:: https://laslabs.com/logo.png
   :alt: LasLabs Inc.
   :target: https://laslabs.com

This module is maintained by LasLabs Inc.
