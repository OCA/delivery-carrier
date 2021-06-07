Create the packages on GLS, which returns a tracking ID.
If there is any kind of mistake (address, weight),
it is possible to cancel it as long as it has not been scanned yet.
If the package is not cancelled, it is invoiced even if it never ships.

When sending a picking, all products should be put in one or multiple packages.
These packages need to have a GLS packaging, either Parcel, Express, or Freight.
These are already pre-configured in the module data.

The end of day report should be printed when the delivery takes place.
At the last resort, this function should be called at the end of the day.
If it had already run, it would have no impact.
In case the delivery is delayed, the report should simply be kept for the
next day, and provided with the next report if there is one.
