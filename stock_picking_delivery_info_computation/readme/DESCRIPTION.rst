This module extends the functionality of delivery to support
calculate weight with preference on the package operations and
also allow you to calculate volume manually with same logic.

On a Picking which only has Inital demand, calculation will be based
on the move lines product quantity.

As soon has *Operations* only will take in count instead of the
previous consideration.

Then all the operation lines and quantity *To Do* quantity will
be the base of calculation if none has totally or partially quantities *Done*.

If any operation has *Done* quantity only this lines will be
on the calculation.
