Here is some methods you can use for your carrier implementation
allowing to have a consistent code accross different carrier modules:

.. code-block:: python

    def _mycarrier_get_sender(...):


    def _mycarrier_get_receiver(...):


    def _mycarrier_get_shipping_date(...):


    def _mycarrier_get_account(...):


    def _mycarrier_get_auth(...):


    def _mycarrier_get_service(...):


    def _mycarrier_convert_address(...):


|


Instead of calling `super()` you can use:

.. code-block:: python

    def _mycarrier_get_service(...):

        result = _roulier_get_service(...)

        result["specific_key"] = "blabla"

        return result
