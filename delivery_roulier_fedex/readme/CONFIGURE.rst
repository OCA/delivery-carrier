* On the FedEx Developer Portal, create a project and retrieve the API Key,
  the Secret Key and the shipping account number (test keys first).
* Inventory > Configuration > Delivery > Carrier Accounts: create a FedEx
  account with the API Key in *Account Number*, the Secret Key in *Account
  Password*, and the 9 digits shipping account in *FedEx Account Number*.
* Set the delivery method *Environment* to test to use the FedEx sandbox.
* The delivery method *Code* is the FedEx ``serviceType``
  (e.g. ``FEDEX_INTERNATIONAL_PRIORITY``).
* Package types should have their dimensions filled in, and products their
  weight, H.S. code and country of origin for international shipments.
* Before going live, the FedEx label certification must be completed with
  the FedEx CT representative.
