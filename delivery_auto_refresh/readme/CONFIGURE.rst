* Activate developer mode.
* Go to *Settings > Technical > Parameters > System Parameters*.
* Locate the setting with key "delivery_auto_refresh.auto_add_delivery_line"
  or create a new one if not exists.
  Put a non Falsy value (1, True...) if you want to add automatically the
  delivery line on save.
* Locate the setting with key "delivery_auto_refresh.refresh_after_picking"
  or create a new one if not exists.
  Put a non Falsy value (1, True...) if you want to refresh delivery price
  after transferring.
