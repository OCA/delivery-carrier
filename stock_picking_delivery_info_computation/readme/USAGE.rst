To use this module, you need to:

#. Go to *Inventory > Operations > Transfers* and
   pick one not in state *Done* or *Cancelled*.
#. Click on tab *Additional Info* and click on button
   *Re-calculate Volume*

If only has Inital demand volume will be based on the move
lines product *Volume* and *Quantity* but if has *Operations*
only will take in count with two possibilities:

#. If none operation has *Done* then Volume is calculate
   as the sum of operation lines *To Do* quantity.
#. As soon any operation line has total of partial *Done*
   quantity only these product volume will be as the
   picking volume.

Weight is always calculate automatic following the standard
but Volume need to click the button to refresh.
