** How does it works ? **


In picking UI a button "Shipping label" trigger label generation 
calling `action_generate_carrier_label()` in models/stock.picking.py


** How to implement my own carrier ? **


Override `generate_shipping_labels()` which is called by previous method
in the same file.
