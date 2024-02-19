To use this module, you need to:

*Configuration:*

1. Configure `partner_resource_delivery_schedule.interval_days` parameter and set
   the days (integer) for the window you want to consider to find an available schedule.
   If parameter doesn't exist, 60 days will be used.

2. Create a new Delivery Schedule on Sales > Configuration > Delivery Schedules menu.


*Sales:*

1. Go to a Customer
2. Click on Enable Delivery Schedule under Sales page
3. Change the Delivery Schedule Calendar or create a new one (Sales Administrators)
4. Create a Sales Order for this Customer with a non Service product with Quantity > 0
5. Click on the button (>>) close to the commitment date (do it several times) and
   check is calculated having in consideration the Availability of this
   Customer resource and Company calendar


*Stock:*

6. On the picking of the previous sale, modify quantity done on the picking in order to
   allow backorder creation
7. Modify the Scheduled date prior today in order to recompute scheduled date of the new
   backorder
8. Create a Backorder
9. Check the Backorder schedule date is calculated having in consideration the
   Availability of the Customer resource and Company calendar
