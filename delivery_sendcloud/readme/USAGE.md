
In short this is how the module works:

- the user creates a sale order in Odoo; the user clicks on "Add shipping" button and selects one of the shipping methods provided by Sendcloud
- when confirming the sale order, a delivery document is generated (stock.picking)
- when confirming the picking, a parcel (or multiple parcels) for the specific sales order are created in Sendcloud under Shipping > Created labels
- the picking is updated with the information from Sendcloud (tracking number, tracking url, label etc...)

## Map of Sendcloud-Odoo data models


| Sendcloud    | Odoo              |
| ----------- |-------------------|
| 
| Brand   | Website Shop      |
| Order   | Sales Order       |
| Shipment   | Picking           |
| Parcel (colli)   | Picking packs     |
| Sender address   | Warehouse address |
| Shipping Method   | Shipping Method                 |



## Multicollo parcels


In Inventory > Configuration > Delivery Packages, set the carrier to Sendcloud.
In the out picking, put the products in different Sendcloud packages to create Multicollo parcels.

## Service Point Picker


The module contains a widget, the Service Point Picker, that allows the selection of the service point.
The widget is placed in the "Sendcloud Shipping" tab of the picking. The widget is visible in case the following is true:

 - the configuration in the Sendcloud panel has the Service Point flag to True (in the Sendcloud integration config)
 - the Shipping Method selected in the picking is provided by Sendcloud
 - the Shipping Method has field sendcloud_service_point_input == "required"
 - all the criteria (from country, to country, weight) match with the current order

## Cancel parcels


When canceling parcels a confirmation popup will ask for confirmation.

## Delivery outside EU


Install either OCA module 'product_harmonized_system' or Enterprise module 'account_intrastat' for delivery outside of EU.
Both include extra field 'country of origin'.


## Troubleshooting


If the communication to the Sendcloud server fails (eg.: while creating a parcel),
the exchanged message is stored in a Log section, under Logging > Actions.