* On the FedEx Developer Portal, create a project and retrieve the API Key,
  the Secret Key and the shipping account number (test keys first).
* Inventory > Configuration > Delivery > Carrier Accounts: create a FedEx
  account with the API Key in *Account Number*, the Secret Key in *Account
  Password*, and the 9 digits shipping account in *FedEx Account Number*.
* Set the delivery method *Environment* to test to use the FedEx sandbox.
* The delivery method *Code* is the FedEx ``serviceType``
  (e.g. ``FEDEX_INTERNATIONAL_PRIORITY``).
* With a thermal doc tab label stock (leading or trailing), choose the
  *FedEx Doc Tab Content* printed on the detachable part of the label:
  *Standard* (references, date, weight, charges) or *Minimum*.
* Enable *FedEx Email Notifications* on the carrier account to let FedEx
  email the tracking number and the shipment progress to the recipient
  (email of the delivery address, or of its parent contact). Choose the
  events to notify and an optional personal message.
* Package types should have their dimensions filled in, and products their
  weight, H.S. code and country of origin for international shipments.
* Before going live, the FedEx label certification must be completed with
  the FedEx CT representative.
