This module allows to generate a unique delivery label/tracking for a whole batch of
pickings.

The batch pickings operations will be grouped in a single delivery package if they are
not already in a delivery package. In case of a batch with multiple packages, a label
per package will be created.

This module is only compatible with `delivery_roulier` carriers.
