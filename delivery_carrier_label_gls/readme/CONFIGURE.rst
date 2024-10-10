To start using GLS, you need to configure two types of settings in
*Inventory - Configuration- Delivery* or *Inventory - Configuration - Settings*
which leads to the right section in inventory global settings.
First you have the *Carrier Account* where you find account number
and password then you also have *Shipping Methods* with other GLS
parameters to configure such as contact ID, urls and return address.
These 2 types of settings use **"GLS"** as delivery type.
The contact ID corresponds to the sender which needs to be a contact in the
GLS database. This determines the default return address, as well as the billing.
You can also configure the tracking url that is used for each carrier.

For client integration tests you need to fill your credentials in the tests/common.py.
