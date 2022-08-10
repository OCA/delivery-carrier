A scheduled action for automating the tracking update for these pickings can be
configured going to *Settings > Technical > Scheduled Actions* and then choosing
*Update deliveries states*. It will update the pending delivery states for the
pickings with service providers with tracking methods configured, and in pending
state (not delivered or cancelled).

In order to send automatic notifications to the customer when the picking is
customer_delivered:

  #. Go to *Inventory > Configuration > Settings*.
  #. Enable the option *Email Confirmation (customer delivered)*.
  #. Choose the template "Delivery: Picking delivered by Email".
