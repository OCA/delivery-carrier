This module extends the functionality of delivery to support
calculating the picking weight giving priority to the package operations and
also allowing you to calculate volume manually with same logic.

On a picking which only has inital demand, calculation will be as standard,
based on the picking lines product quantity.

As soon as you have any reserved quantity, it will only take them into account.
In this case, the computation of the weight and volume is based in *to do*
quantities, unles you introduce anything in *done* quantity, switching to this
column in that case.

The volume is auto-computed when the picking is generated from a sales order,
or a backorder is created from original picking, but remains editable for any
possible manual edition.

You also have a button available for recomputing volume with current data.
