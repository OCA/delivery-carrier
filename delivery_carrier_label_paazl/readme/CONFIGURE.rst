To configure this module, you need to:

#. Add options to your paazl carrier
#. Add a carrier account with delivery type ``paazl``, fill in your webshop id as account number, and the integration password as password. You find those values in Integrations/SOAP API on paazl's website
#. If you want to receive status updates (including the carrier's tracking url), you need to enable the push API in your paazl account, and fill in ``https://$yourdomain/_paazl/push_api/v1`` as notification URL. You should enable client authentication and fill in the token generated there in the `Bearer token` field of the carrier account in Odoo
