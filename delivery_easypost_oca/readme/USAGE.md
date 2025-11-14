**Workflow 1: Calculate Shipping Rates on Sale Order**

1.  Create a new **Sale Order**: Go to **Sales → Orders → Quotations →
    Create**
2.  Add products to the order (ensure products have weight configured)
3.  Set the **Customer** with a complete shipping address
4.  Click the **Add Shipping** button
5.  In the **Add a shipping method** wizard:
    - Select your **Easypost OCA** delivery method from the list
    - Click **Get Rate** button
6.  The system will:
    - Query EasyPost API with order details (weight, origin/destination
      addresses)
    - Automatically select the lowest rate from all available carriers
    - Add a shipping line to the order with the carrier name (e.g.,
      "Easypost - USPS Priority")
7.  The **Sale Order** now shows:
    - Shipping line with carrier name and calculated price
    - Stored data: shipment_id, rate_id, carrier_name (for later
      shipment creation)
8.  Confirm the order when ready to proceed

**Workflow 2: Generate Shipping Labels (Single Package)**

1.  After confirming the sale order, a **Delivery Order** is
    automatically created
2.  Go to **Inventory → Delivery Orders** and open the delivery order
3.  Click **Check Availability** to reserve stock
4.  Set the **Done** quantities for each product line
5.  Click **Validate** button - the system will automatically:
    - Create an EasyPost shipment using the stored rate (or calculate a
      new rate if expired)
    - Purchase the shipment (charges your EasyPost account)
    - Download the shipping label in your configured format
      (PDF/ZPL/EPL2)
    - Attach the label to the picking in the **Chatter** messages
    - Set the tracking number on the delivery order
6.  Find the shipping label in the **Chatter** section at the bottom
7.  Click the attachment to download and print the label
8.  Attach the printed label to your package and ship

**Workflow 3: Multi-Package Shipments**

If your delivery order contains multiple packages:

1.  In the delivery order, after setting **Done** quantities

2.  Use the **Put in Pack** button to create packages:

    - Select products for the first package
    - Click **Put in Pack** - creates Package 1
    - Repeat for additional packages

3.  Click **Validate** - behavior depends on your carrier configuration:

    **Shipments Mode** (default):

    - Creates individual EasyPost shipment for each package
    - Each package gets its own tracking number
    - Each package is charged separately
    - System generates a single merged PDF/ZPL with all labels in
      sequence

    **Batch Mode**:

    - Creates a batch shipment containing all packages
    - Packages are purchased together in a single transaction
    - May provide better rates for bulk shipping
    - Single merged label file with all package labels

4.  All tracking numbers are displayed in the delivery order
    (comma-separated)

5.  The merged label file contains all package labels - print and attach
    to corresponding packages

**Workflow 4: Track Shipments**

After shipment creation:

1.  Open the **Delivery Order**
2.  Click the **Tracking** button/link in the form
3.  Opens the EasyPost tracking page in a new browser tab
4.  View real-time shipment status, location history, and delivery
    confirmation

**Using Product Packaging for Accurate Rates**

To use carrier-specific package types (flat rate boxes, envelopes,
etc.):

1.  In the delivery order, after using **Put in Pack**
2.  Edit the created **Package** record
3.  Set the **Packaging** field to a product packaging configured for
    EasyPost (see CONFIGURE.rst)
4.  The packaging dimensions and shipper package code are sent to
    EasyPost
5.  Results in more accurate rates and ensures carrier compatibility

**Label Format Guide**

Choose the appropriate label format for your printing setup:

- **PDF Format**:
  - Works with all standard printers
  - Can preview in browser before printing
  - Best for offices with regular laser/inkjet printers
  - Label size: typically 8.5"x11" or 4"x6"
- **ZPL Format**:
  - For Zebra thermal label printers
  - Direct thermal printing (no ink/toner required)
  - Common in warehouses and shipping departments
  - Requires ZPL-compatible thermal printer
- **EPL2 Format**:
  - For legacy Eltron and older Zebra thermal printers
  - Use only if your printer doesn't support ZPL
  - Less common in modern shipping operations

**Important Usage Notes**

- **Product Weight Required**: All products in the order must have
  weight configured. Orders without weight cannot calculate shipping
  rates.
- **Complete Addresses Required**: Both warehouse address (ship from)
  and customer address (ship to) must be complete with street, city,
  state/province, ZIP, and country.
- **Test Mode Shipments**: Shipments created in test mode (with test API
  key) are not actually shipped. They are mock shipments for testing
  purposes and no charges apply.
- **Cannot Cancel Shipments**: EasyPost shipments cannot be cancelled
  through Odoo. Some carriers allow refunds within 24 hours - use the
  EasyPost dashboard for refund requests.
- **Rate Expiration**: Shipping rates may change between quotation and
  shipment if significant time has passed. The system will automatically
  recalculate rates at shipping time if the stored rate has expired.
- **Multiple Carriers**: EasyPost automatically compares rates from
  multiple carriers (USPS, UPS, FedEx, etc.) and selects the lowest
  rate. You can see the selected carrier name in the shipping line
  (e.g., "Easypost - USPS Priority").
- **Tracking Updates**: Tracking information is available immediately
  after shipment creation. Real tracking events (scans, delivery) appear
  as the carrier processes the shipment.
