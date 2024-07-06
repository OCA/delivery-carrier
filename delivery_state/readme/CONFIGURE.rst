A scheduled action for automating the tracking update for these pickings can be
configured going to *Settings > Technical > Scheduled Actions* and then choosing
*Update deliveries states*. It will update the pending delivery states for the
pickings with service providers with tracking methods configured, and in pending
state (not delivered or cancelled).

In order to send automatic notifications to the customer when the picking is
confirmed:

  #. Go to *Inventory > Configuration > Settings*.
  #. Enable the option *Email Confirmation*.
  #. Choose the template "Delivery State Notification to Customer".

In order to deactivate the automatic update of the carrier state in a shipping
method:

  #. Go to *Inventory > Configuration > Shipping Methods*.
  #. Go to the form view of the shipping method.
  #. Uncheck the "Track Carrier State" option.
