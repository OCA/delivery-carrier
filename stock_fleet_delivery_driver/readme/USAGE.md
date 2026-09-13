## Basic configuration
1. Go to Inventory > Configuration > Settings and activate Dispatch Management System.
1. Go to Fleet App and create new Vehicle or choose one already created.
1. Add a Driver and a Category (with weight and volume limits) to the Vehicle.
1. Go to Inventory > Configuration > Delivery > Delivery Methods.
1. Create new Delivery Method or choose one already created.
1. Add a Vehicle to the Delivery Method.

## Sale Flow
1. Go to Sales > Orders > Quotations.
1. Create new Sale Order with non Service product with Quantity > 1.
1. Click on Add Shipping button and choose one with a Vehicle.
1. Confirm Sale Order.
1. Vehicle was automatically assigned in picking from selected Carrier.
1. You can change the Vehicle without changing the Carrier.

## Stock Flow
1. Go to Inventory > Operations > Transfers > Deliveries.
1. Create new Transfer.
1. Choose a Carrier.
1. The Vehicle is automatically assigned.
1. You can change the Vehicle without changing the Carrier.

## Batch Flow
1. Add multiple Transfers that has Vehicles to a Batch.
1. The Vehicle is selected based on the most repeated in the Transfers.
1. The Driver is selected based on the most repeated in the Transfers.

## Auto Batch Flow
1. Go to Inventory > Configuration > Operation Types.
1. Select an operation type.
1. Activate Automatic Batches.
1. Choose Vehicle and/or Driver in the batch grouping.
1. Create and confirm pickings with the same vehicle/driver.
1. The pickings are batched automatically depends their vehicle/driver.
