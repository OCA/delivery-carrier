## Calculating Shipping Rates on Sales Orders
1. Create or open a **Sales Order** and click **Add shipping**.
2. Select **Dachser** and click **Get rate** to fetch the live quotation from Dachser REST API v2.
3. Click **Add** to create the delivery line on the sales order.

## Sending Shipments & Printing Labels from Pickings
1. Validate the outgoing **Delivery Order** (`stock.picking`) or click **Send to Shipper**.
2. Odoo sends the transport order to Dachser, assigns **SSCC** codes to the packages, updates `delivery_state` and `tracking_state_history`, records `carrier_tracking_ref`, and attaches the **PDF/ZPL label** in the chatter.
3. From the picking form you can also:
   - Click **Dachser Label** to reprint PDF/ZPL labels.
   - Click **Send to Dachser TMS** when the order was created in `imported` or `labelled` state.
   - Click **Print Return Label** to generate a Dachser return label.
   - Use **Tracking** to open Dachser eLogistics ShipmentPointer, or rely on `delivery_state`'s scheduled action (`tracking_state_update`) to automatically synchronize `delivery_state`, `tracking_state_history`, and download the signed **POD PDF** into `pod_file`.

## Downloading the Daily Loading Manifest (Transfer List)
1. Open the Dachser shipping method and click the **Daily Manifest** smart button.
2. Select the **Order Date** (and optional **Order Group**) and click **Query and Download PDF Manifest**.
