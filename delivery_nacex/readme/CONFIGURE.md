1.  Go to **Inventory > Configuration > Carrier Accounts** and create a new
    account with:
    - **Delivery Type**: NACEX
    - **Account Number**: Your NACEX API username
    - **Account Password**: Your NACEX API password

2.  Go to **Inventory > Configuration > Delivery Methods** and create a new
    carrier with **Provider** set to *NACEX*.

3.  In the carrier form, select the **Account** created in step 1.

4.  In the **NACEX Configuration** tab, fill in:
    - **Customer Agency**: Your default NACEX agency code (fallback)
    - **Customer Code**: Your NACEX customer number
    - **Service Code**: The desired NACEX service type
    - **Carriage Code**: Origin, Destination, or Third-party
    - **Packaging Code**: Document, Bag, or Package

5.  Optionally, go to **Inventory > Configuration > Carrier Agencies** and
    create agencies with **Delivery Type** set to *NACEX*. Set the
    **External Reference** to the NACEX agency code and assign the relevant
    **Warehouses**. When configured, the agency code is resolved
    automatically per picking based on the source warehouse, instead of
    using the default from the carrier.
