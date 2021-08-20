These are the operations possible with this module:

Place shipping bookings
~~~~~~~~~~~~~~~~~~~~~~~

#. When the picking is validated, the shipping will be booked at Schenker.
#. With the response, we'll receive the delivery tracking number and the pdf label in a
   chatter message and it will be kept as attachment to the document.
#. You can manage packages number either with the proper Odoo workflows or with the
   package number field available in the *Additional Info* tab. You'll get as many
   labels as declared packages.

Cancel bookings
~~~~~~~~~~~~~~~

#. As in other carriers, we can cancel the shipping after the picking is done. To do
   so, go to *Additional Info* tab and click on the *Cancel* action on the side of the
   tracking number.
#. We can generate a new shipping if necessary.

Get labels
~~~~~~~~~~

#. If by chance we delete the generated labels, we can obtain them again hitting the
   *Schenker Label* buttons in the header of the picking form.

Tracking
~~~~~~~~

#. The module is integrated with `delivery_state` to be able to get the tracking info
   directly from the DB Schenker API.
#. To do so, go to a picking shipped with Schenker. In the *Additional Info* tab you'll
   find an action button to *Update tracking state* so the state will be updated from
   the Schenker API.

Debugging
~~~~~~~~~

The API calls and responses are tracked in two special fields in the picking that can
be viewed by technical users. You can also log them in as `ir.logging` records setting
the carrier debug on from the smart button.
