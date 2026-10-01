To configure this module, you need to:

1.  Add a Shipping Method with Provider ``UPS`` and fill in your UPS credentials
    (Client ID and Client Secret)
2.  Configure in Odoo all required fields of the UPS tab with your
    account data <https://wwwapps.ups.com/ppc/ppc.html> (Shipper number,
    Default Packaging, Package Dimension Code, Package Weight Code and
    File Format).
3.  If you have "Tracking state update sync" checked all delivery orders
    state check will be done querying UPS services.
4.  It is possible to create a UPS carrier for cash on delivery parcels.
    Select the `ups` delivery type and check the "Cash on Delivery"
    checkbox under the "UPS" tab. It is required to select the "UPS COD
    Funds Code" when the "Cash on Delivery" option is selected.
5.  The "Negotiated Rates" checkbox is disabled by default. When checked 
    and your account has negotiated rates, UPS will use your
    account's negotiated rates for shipping cost calculations.
6.  Optionally, set a "Declared Value (%)" under the "UPS" tab.
    When set, delivery orders using this carrier pre-fill a declared
    value for shipping insurance, computed as this percentage of the
    taxed value of the shipped goods (taken from the sale order lines).

**NOTE** You need to add an app from <https://developer.ups.com/> for
using the webservice.
