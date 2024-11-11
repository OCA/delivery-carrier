To use this module, you need to:

* Identify your SSCC range. For example: `123456789012xxxxx`.
* Go to the form view of the `ir.sequence` record for your packages.
* Clear the Prefix field (eg from `PACK` to empty)
* Set the Sequence Size (padding) field to the number of variable digits.
  In the above example, it would be 5.
* Go to the Python tab
* Enable the 'Use Python' checkbox
* Change the default 'number' expression to:

.. code-block:: python

   # Note that you have to adapt this to your own range.
   "123456789012" + number_padded + str(get_barcode_check_digit("123456789012" + number_padded + "x"))

Now, your packages will generate with SSCC codes instead of regular sequence numbers such as PACK00001.
Once the numbers run out, you'll have to configure this again with a new sequence.
