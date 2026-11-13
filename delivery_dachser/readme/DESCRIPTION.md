This module integrates Odoo's `delivery` framework (along with `delivery_package_number`, `delivery_state`, and `stock_picking_volume`) with **Dachser REST API v2** (`https://api-gateway.dachser.com/rest/v2`), providing European Logistics (`T`) and Food Logistics (`F`) shipping automation:

- **Online Freight Quotations (`sale.order`)**:
  - Live rate calculation via `POST /rest/v2/quotations` with currency conversion and automatic Incoterm-to-Frankatur mapping (`EXW`, `FCA`, `DAP`, `DDP`, etc.).
  - Compatible with OCA `delivery_price_method` when fixed or rule-based local pricing is desired.
- **Shipment & Picking Submission (`stock.picking`)**:
  - Transport order creation (`POST /rest/v2/transportorders/{basket}`) in `imported`, `labelled`, or `sent` baskets, plus standalone label generation (`POST /rest/v2/labels`) with automatic test-environment fallback.
  - Native integration with `delivery_package_number` (`number_of_packages`), `delivery_state` (`delivery_state`, `tracking_state`, `tracking_state_history`, `tracking_json`, `date_delivered`, `pod_file`), and `stock_picking_volume` (`volume`).
  - Automatic assignment of 18-digit **GS1 SSCC** codes to physical Odoo packages (`stock.quant.package`).
  - Automatic 30-character street and name splitting complying with Dachser REST API v2 schema constraints.
- **Label Generation (PDF & Thermal ZPL)**:
  - Instant attachment of **PDF** (`P`) or **ZPL** (`Z`) shipping labels on the picking, supporting GS1 **EAN** 1D barcodes and **2D DataMatrix (DMC)** labels.
  - One-click label reprinting (`dachser_get_label`), deferred TMS confirmation (`dachser_send_to_tms`), and return label generation (`dachser_get_return_label`).
- **Live Tracking, Event History & Signed POD**:
  - Direct link to **Dachser eLogistics ShipmentPointer**.
  - Live shipment status (`GET /rest/v2/shipmentstatus`), full chronological event history (`GET /rest/v2/shipmenthistory`), and automatic signed **Proof of Delivery (POD PDF)** download (`GET /rest/v2/pods`) stored in `delivery_state`'s `pod_file`.
- **Daily Loading Manifest (Transfer List)**:
  - Wizard to download the daily **Transfer List PDF** (`GET /rest/v2/transferlists/{orderdate}`) for the Dachser driver.
