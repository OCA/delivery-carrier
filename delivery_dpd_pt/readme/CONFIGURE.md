1.  Go to **Inventory > Configuration > Carrier Accounts** and create a new
    account with:
    - **Delivery Type**: DPD Portugal
    - **Account Number**: DPD API username
    - **Account Password**: DPD API password
    - **DPD OAuth Client ID** and **DPD OAuth Client Secret**: credentials of
      the OAuth application provided by DPD

2.  Go to **Inventory > Configuration > Delivery Methods** and create a new
    carrier with **Provider** set to *DPD Portugal*.

3.  In the carrier form, select the **Account** created in step 1, then open
    the **DPD Portugal Configuration** tab and set:
    - **DPD Sub-Account**: the 8-digit DPD sub-account used to register
      shipments
    - **DPD Sender Contact**: the contact person printed on labels
      (defaults to the company partner)
    - **DPD Agreed Price**: price agreed with DPD, used for shipping costs
      (the DPD API does not provide rating)
    - **DPD Label Format**: A4 one label, A4 two labels, or thermal
      10 x 15 cm ZPL
    - **DPD Predict Delivery**: request DPD Predict notifications
    - **Hide Recipient Phone/Email on Label**: omit contact data from labels

4.  Click the **Test Environment** smart button at the top of the form to
    toggle to **Production Environment** when ready for live shipments.
    The production endpoint is inferred from DPD examples; confirm the
    production URL and credentials with DPD before using it.
