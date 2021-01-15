Depending on the delivery service provider, the state tracking could be more or
less complete, since it could have or not the necessary API calls implemented.

With regular methods (fixed, based on rules):

  #. Go to Inventory / Operations and open an outgoing pending picking.
  #. In the *Additional Info* tab, assign it a delivery carrier which is fixed or
     based on rules.
  #. Validate the picking and you'll see in the same tab the delivery state
     info with the shipping date and the shipping state.
  #. If enabled, an automatic notification will be sent to the picking customer.

When service provider methods are implemented, we can follow the same steps as
described before, but we'll get additionally:

  #. In the *Additional Info* tab, we'll see button *Update tracking state* to
     manually query the provider API for tracking updates for this expedition.
  #. Depending on the stated returned by the provider, we could get these
     states (field *Carrier State*):

        * Shipping recorded in carrier
        * In transit
        * Canceled shipment (finished)
        * Incidence
        * Warehouse delivered
        * Customer delivered (finished)
  #. In the field *Tracking state* we'll get the tracking state name given by
     the provider (which is mapped to the ones in this module)
  #. In the field *Tracking history* we'll get the former states log.
