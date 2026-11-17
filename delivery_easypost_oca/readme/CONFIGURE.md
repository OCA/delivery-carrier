**Step 1: Configure Delivery Carrier**

1.  Go to **Inventory → Configuration → Delivery Methods**
2.  Create a new delivery method or edit an existing one
3.  Set **Provider** to **Easypost OCA**
4.  In the **Easypost Configuration** tab, configure the following
    fields:
    - **Easypost Test API Key**: Your test API key from EasyPost
      dashboard (for development and testing)
    - **Easypost Production API Key**: Your production API key (for live
      shipments)
    - **Label Format**: Choose the label format according to your
      printer:
      - **PDF** (default): Standard format, works with all printers
      - **ZPL**: For Zebra thermal printers (direct thermal printing)
      - **EPL2**: For legacy Eltron/Zebra thermal printers
    - **Delivery Multiple Packages**: Select the shipping strategy for
      orders with multiple packages:
      - **Shipments** (default): Create individual shipment for each
        package, charged separately
      - **Batch**: Create batch shipment with all packages in a single
        transaction
5.  Configure **Pricing** tab as needed (fixed price, percentage, or
    formula-based)
6.  Enable the **Test Environment** checkbox during development to use
    test API key
7.  **Save** the delivery method

**Step 2: Configure Product Packaging (Optional)**

For accurate shipping calculations using carrier-specific package types:

1.  Go to **Inventory → Configuration → Product Packagings**
2.  Create or edit a product packaging
3.  Set **Carrier** to **Easypost OCA**
4.  Configure package dimensions: **Length**, **Width**, **Height** (in
    inches)
5.  Set **Shipper Package Code** for carrier-specific packaging (e.g.,
    "Parcel", "FedExBox", "FlatRateEnvelope")
6.  Set **Carrier Prefix** to filter by specific carrier if needed
    (e.g., "USPS", "FedEx")
7.  **Save** the packaging

**Step 3: Configure Warehouse Address**

Ensure your warehouse has a complete address that will be used as the
shipper address:

1.  Go to **Inventory → Configuration → Warehouses**
2.  Edit your warehouse
3.  Set complete **Address** with all required fields:
    - Street address
    - City
    - State/Province
    - ZIP/Postal code
    - Country
4.  Verify the address is accurate - this will be the "Ship From"
    address on all labels

**Step 4: Enable API Logging (Optional)**

For debugging API interactions and troubleshooting issues:

1.  Edit the delivery carrier configured in Step 1
2.  Go to the **Advanced Options** tab
3.  Enable **Log XML** checkbox
4.  Check API request/response logs at **Settings → Technical →
    Logging**

**Important Configuration Notes**

- **Test vs Production Mode**: Toggle the **Test Environment** checkbox
  to switch between test and production API keys. Always test thoroughly
  in test mode before going live.
- **Weight Units**: The module automatically converts product weights to
  ounces (EasyPost requirement). Ensure all products have weight
  configured.
- **Currency Conversion**: EasyPost returns rates in USD. The module
  automatically converts to the order's currency using Odoo's currency
  rates.
- **USPS/UPS End Shipper**: These carriers require an end shipper ID for
  certain services. The module automatically creates and manages this -
  no manual configuration needed.
- **API Keys Security**: Keep your production API key secure. Never
  commit API keys to version control or share them publicly.
- **Rate Caching**: EasyPost rates are calculated in real-time. Rates
  shown at quotation time may differ slightly at shipping time if time
  has passed.
