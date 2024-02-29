To configure this module, you need to:

#. Add a carrier account with delivery type ``ups`` and fill in your credentials (UPS
   Client and UPS Client Secret)
#. Configure in Odoo all required fields of the UPS tab with your account data
   https://wwwapps.ups.com/ppc/ppc.html (Shipper number, Default Packaging, Package
   Dimension Code, Package Weight Code and File Format).
#. If yo have "Tracking state update sync" checked all delivery orders state check will
   be done querying UPS services.
#. It is possible to create a UPS carrier for cash on delivery parcels. Select the
   ``ups`` delivery type and check the "Cash on Delivery" checkbox under the "UPS" tab.
   It is required to select the "UPS COD Funds Code" when the "Cash on Delivery" option
   is selected.

**NOTE** You need to add an APP from https://developer.ups.com/ for using the
webservice.
