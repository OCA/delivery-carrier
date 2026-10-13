To configure this module, you need to:

1.  Add a Shipping Method with Provider ``UPS`` and fill in your UPS credentials
    (Client ID and Client Secret)
2.  Configure in Odoo all required fields of the UPS tab with your
    account data <https://wwwapps.ups.com/ppc/ppc.html> (Shipper number,
    Default Packaging, Package Dimension Code, Package Weight Code and
    File Format).
3.  If yo have "Tracking state update sync" checked all delivery orders
    state check will be done querying UPS services.
4.  It is possible to create a UPS carrier for cash on delivery parcels.
    Select the `ups` delivery type and check the "Cash on Delivery"
    checkbox under the "UPS" tab. It is required to select the "UPS COD
    Funds Code" when the "Cash on Delivery" option is selected.
5.  The "Negotiated Rates" checkbox is disabled by default. When checked
    and your account has negotiated rates, UPS will use your
    account's negotiated rates for shipping cost calculations.
6.  To enable UPS Global Checkout (landed cost), under the "UPS" tab in
    the "Global Checkout (Landed Cost)" group:
    - Set "UPS Global Checkout Countries" with the destination country
      groups that UPS has enabled for your account. Landed cost is only
      requested for destinations in these groups; leaving it empty
      disables the feature.
    - Set "UPS Tariffs/Duties Product": the product used for the separate
      duties and taxes order line. Configure its taxes appropriately for
      imported duties (usually no additional tax). If left empty, no
      landed cost line is added to the order (the quote is still
      generated and stored).

**NOTE** You need to add an app from <https://developer.ups.com/> for
using the webservice.

**NOTE** UPS Global Checkout is a contract-only service. Contact the UPS
Global Checkout onboarding team to have it enabled on your account before
configuring it in Odoo.

**NOTE** For more accurate landed cost calculations, install the OCA
``product_harmonized_system`` module and set an H.S. Code on your products
(or their categories). When a code is resolved through that module, the
full national code (including extension digits beyond the 6-digit HS
heading) is sent to UPS Global Checkout. Otherwise the module falls back
to the core ``hs_code`` field (from ``stock_delivery``, typically 6
digits). If no HS code can be resolved at all, none is sent and UPS
classifies the goods from their description.
