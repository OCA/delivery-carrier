This custom module carrier_deutsche_post allows to purchase shipping label from Deutsche Post (German Post) directly in Odoo. Several "products" of Deutsche Post can be configured.

Appropriate delivery orders (in module Warehouse) show a Buy Deutsche Post Label button. When clicking that button, a shipping label from Deutsche Post is bought online. It is presented to the user as PDF and also attached to the delivery order. For international shipments this PDF can contain a 2nd page with an automatic generated CN 22 form. The CN 22 form is filled by carrier_deutsche_post automatically, depending on the products being shipped.

The Buy Deutsche Post Label button is also displayed in Barcode view.

Required settings: Button "Buy Deutsche Post Label" is being invisible when carrier_type field is False. carrier_type is a related field so make sure that you set the Default Carrier in picking and Type in that Carrier (Delivery Method).

To setup carrier accounts go to Inventory -> Configuration -> Carrier Accounts

.. image:: images/1_carrier_accounts.png

Click on Create to create carrier accounts

.. image:: images/2_settings_carrier_accounts.png

If you want to edit the delivery methods go to Inventory -> Configuration -> Delivery Methods

.. image:: images/3_delivery_methods.png

Click on Create to create delivery methods

.. image:: images/4_settings_delivery_methods.png

To purchase a Deutsche Post label go to Sales -> click on a Sales Order -> Delivery -> Buy Deutsche Post label

.. image:: images/5_buy_label.png

Bought Deutsche Post labels are attached to delivery orders in tab Additional Info

.. image:: images/6_attachment.png

PDF label germany

.. image:: images/7_germany.png

PDF label international

.. image:: images/8_international.png

**Operations**

The API of Deutsche Post requires to provide prices within requests. Deutsche Post changes their prices every few months. Prices are not gathered dynamically but are hard coded in `inema library <https://pypi.org/project/inema/>`_. Inema supports multiple price lists in parallel but (Python) requires a restart to take those new price lists into account. In consequence, this means for operation:

1. Monitor price changes of Deutsche Post. Usually when being a Portokasse customer, you should receive an email a few weeks in advance with a new price list (CSV) attached.
2. Make sure the new prices are added to inema and that inema version is ideally released. Usually inema's maintainers are helpful in updating those promptly.
3. Update your Odoo system with the required inema version.
4. At the day when new prices come into affect, restart your Odoo system.

If you receive an unknown error, there is a high chance that it's related to an invalid price.
