To carry out the shipment, the shipping method previously created must be set on the delivery order:

- Once the outgoing delivery is “Validated (Done)", the shipping information is automatically transmitted to CBL. If everything is correct, a tracking number and the corresponding labels are generated.
- Shipments can be cancelled by clicking the "Cancel" button located next to the picking's tracking number. Keep in mind that using a carrier with the "Needs Confirmation" option unchecked, while having the opposite configuration set in CBL, may cause issues when attempting to cancel a shipment. In such cases, contact CBL so they can adjust the confirmation policy accordingly.
- If a shipment could not be generated or has been cancelled, a new one can be created by clicking the "Send to Shipper" button at the top of the stock picking.
- Shipments that require confirmation after the tracking number has been assigned can be confirmed as follows:
   - Individually: By clicking the "Confirm" button in the "Tracking Number" field, located under the "Additional Info" tab within the "Shipping Information" section.
   - [Improved] Bulk method: In the list view of outgoing deliveries, select all deliveries for the carrier whose status is “Validated (Done)", click the "Actions" gear icon → "Confirm CBL pickings". A wizard will appear listing the deliveries to be confirmed. Verify that all required pickings are included, then click the "Confirm Shipments" button.
   - Additionally, there is a scheduled action ("CBL: Confirm Shipments") that automatically validates pending CBL shipments once per day by default.
- To generate the manifest, you need to Inventory > Operation > Manifest, select a CBL carrier and set the date range to select the picking.
