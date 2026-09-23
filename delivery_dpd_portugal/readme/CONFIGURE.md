1.  Go to **Inventory > Configuration > Carrier Accounts** and create a new
    account with:
    - **Delivery Type**: DPD Portugal
    - **Account Number**: Your DPD Portugal API username
    - **Account Password**: Your DPD Portugal API password

2.  Go to **Inventory > Configuration > Delivery Methods** and create a new
    carrier with **Provider** set to *DPD Portugal*.

3.  In the carrier form, select the **Account** created in step 1.

4.  Click the **Test Environment** smart button at the top of the form to toggle
    to **Production Environment** when ready for live shipments.

5.  In the **DPD Portugal Configuration** tab, configure:
    - **Service Type**: Standard, Express, or Economy
    - **Label Format**: PDF or ZPL
    - **Default Package Type**: Optional default package dimensions
    - **Package Weight Unit**: KG or LB
    - **Package Dimension Unit**: CM or IN

6.  Configure **Additional Services** as needed:
    - **Enable COD**: Cash on delivery functionality
    - **Enable Insurance**: Shipping insurance with default amount
    - **Saturday Delivery**: Enable Saturday delivery option
    - **Predict Service**: Enable DPD Predict notifications

7.  Optionally, go to **Inventory > Configuration > Carrier Agencies** and
    create agencies with **Delivery Type** set to *DPD Portugal*. Set the
    **External Reference** to the DPD agency code and assign the relevant
    **Warehouses**. When configured, the agency code is resolved
    automatically per picking based on the source warehouse.
