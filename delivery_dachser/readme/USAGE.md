## Calculating Shipping Rates on Sales Orders
1. Create or open a **Sales Order** and click **Add shipping**.
2. Select **Dachser** and click **Get rate**.
3. The wizard displays the **Internal Estimated Cost**, **Chargeable Weight**, and a detailed **Dachser Quotation Breakdown** (either from Dachser's `quotations` API or from the matching local tariff rule).
4. Click **Add** to apply the shipping line and store the internal cost on the order.

## Sending Shipments & Printing Labels from Pickings
1. Validate the outgoing **Delivery Order** (`stock.picking`) or click **Send to Shipper**.
2. Odoo sends the transport order to Dachser, assigns **SSCC** codes to the packages, updates `delivery_state` and `tracking_state_history`, records the tracking reference and **eLogistics ShipmentPointer** URL, and attaches the **PDF/ZPL label** in the chatter.
3. In the **Dachser Logistics** tab of the picking, you can:
   - Click **Confirm Order to Dachser TMS** (when created in `imported` or `labelled` state).
   - Click **Dachser Label** to reprint PDF/ZPL labels.
   - Click **Update Dachser Tracking** (or use `delivery_state`'s tracking update) to fetch live status and event history.
   - Click **Download POD** to attach the signed Proof of Delivery PDF and populate `pod_file`.
   - Click **Fetch Actual Invoiced Costs** to compare Dachser's invoiced freight cost against the estimated cost.
   - Click **Check LDR Route** to verify the Dachser destination routing code.

## Downloading the Daily Loading Manifest (Transfer List)
1. Open the Dachser shipping method and click the **Manifest / Transfer List** smart button.
2. Select the **Order Date** (and optional **Order Group**) and click **Query and Download PDF Manifest**.
